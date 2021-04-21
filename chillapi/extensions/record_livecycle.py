from datetime import datetime

from chillapi.abc import TableExtension
from chillapi.database.query_builder import create_select_join_soft_delete_filter
from chillapi.exceptions.api_manager import ConfigError


class SoftDeleteExtension(TableExtension):
    def add_query_filter(self, query: dict, query_values: dict):
        _field = self.config['default_field']
        query = {**query, **{_field: {'op': 'isnull', 'value': None}}}
        query_values = {**query_values, **{_field: None}}

        return query, query_values

    def unset_field_data(self, form_data):
        _field = self.config['default_field']
        del form_data[_field]
        return form_data

    def _walk_cascade_options(self, one_to_many: callable, many_to_many: callable):
        if 'cascade' in self.config:
            _cascades = self.config['cascade']
            if 'one_to_many' in _cascades:
                _one_to_many = _cascades['one_to_many']
                for _otm, _relation in enumerate(_one_to_many):
                    _relation_table = _relation['table']
                    _pk = _relation['column_id']
                    _fk = _relation['column_fk']
                    one_to_many(_relation_table = _relation_table, _pk = _pk, _fk = _fk, _inspector = self.inspector,
                                _extension_field = self.config['default_field'])

            if 'many_to_many' in _cascades:
                _one_to_many = _cascades['many_to_many']
                for _otm, _relation in enumerate(_one_to_many):
                    _relation_table = _relation['table']
                    _relation_join_table = _relation['join_table']
                    _pk = _relation['column_id']
                    _relation_columns = _relation['join_columns']
                    many_to_many(_relation_table = _relation_table, _pk = _pk, _relation_join_table = _relation_join_table,
                                 _relation_columns = _relation_columns, _inspector = self.inspector,
                                 _repository = self.repository, _extension_field = self.config['default_field'])

    def validate(self):
        super().validate()

        def one_to_many(**args):
            _relation_table = args['_relation_table']
            _pk = args['_pk']
            _fk = args['_fk']
            _inspector = args['_inspector']
            if not _inspector.has_table(_relation_table):
                raise ConfigError(f'{_relation_table} does not exists!')

            _relation_table_columns = map(lambda x: x['name'], _inspector.get_columns(_relation_table))
            if _pk not in _relation_table_columns:
                raise ConfigError(f'column_id: {_pk} in {_relation_table} does not exists!')
            if _fk not in _relation_table_columns:
                raise ConfigError(f'column_fk: {_pk} in {_relation_table} does not exists!')

        def many_to_many(**args):
            _relation_table = args['_relation_table']
            _relation_join_table = args['_relation_join_table']
            _pk = args['_pk']
            _relation_columns = args['_relation_columns']
            _inspector = args['_inspector']

            if not _inspector.has_table(_relation_table):
                raise ConfigError(f'{_relation_table} Table does not exists!')
            if not _inspector.has_table(_relation_join_table):
                raise ConfigError(f'{_relation_table} Table does not exists!')
            _relation_table_columns = [x['name'] for x in _inspector.get_columns(_relation_table)]
            _relation_join_table_columns = [x['name'] for x in _inspector.get_columns(_relation_join_table)]

            if _pk not in _relation_table_columns:
                raise ConfigError(f'column_id: {_pk} in Table {_relation_table} does not exists!')

            if _relation_columns['main'] not in _relation_join_table_columns:
                raise ConfigError(
                        f'join_columns[main]: {_relation_columns["main"]} in Table {_relation_join_table} does not exists!')

            if _relation_columns['join'] not in _relation_join_table_columns:
                raise ConfigError(
                        f'join_columns[join]: {_relation_columns["join"]} in Table {_relation_join_table} does not exists!')

        self._walk_cascade_options(one_to_many = one_to_many, many_to_many = many_to_many)

    def soft_delete(self, id_field, id, response):
        def one_to_many(**args):
            _relation_table = args['_relation_table']
            _pk = args['_pk']
            _fk = args['_fk']
            _repository = args['_repository']
            _extension_field = args['_extension_field']
            _relation_ids = _repository.fetch_by(
                    _relation_table,
                    [_pk],
                    {_fk: {'op': '=', 'value': id}},
                    {_fk: id}
                    )
            _cascade_ids = [x[0] for x in _relation_ids.fetchall()]
            soft_deletes_one_to_many = [{_extension_field: now, _pk: x} for x in _cascade_ids]
            _repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field = _pk)

        def many_to_many(**args):
            _relation_table = args['_relation_table']
            _relation_join_table = args['_relation_join_table']
            _pk = args['_pk']
            _relation_columns = args['_relation_columns']
            _repository = args['_repository']
            _extension_field = args['_extension_field']
            sql = create_select_join_soft_delete_filter(_relation_table, _pk,
                                                        _relation_join_table, _relation_columns)
            _relation_ids = self.repository.execute(sql, {'id': id})
            _cascade_ids = [x[0] for x in _relation_ids.fetchall()]
            soft_deletes_one_to_many = [{_extension_field: now, _pk: x} for x in _cascade_ids]
            _repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field = _pk)

        now = datetime.now().isoformat()
        _field = self.config['default_field']
        self.repository.update_record(
                self.table,
                id_field,
                id,
                {id_field: id, _field: now}
                )

        self._walk_cascade_options(one_to_many = one_to_many, many_to_many = many_to_many)

        response.response['message'] = 'ok'
        response.response['code'] = 200

        return response

    def soft_delete_batch(self, table_name, extension_field, id_field, data):
        def one_to_many(**args):
            _relation_table = args['_relation_table']
            _pk = args['_pk']
            _fk = args['_fk']
            _repository = args['_repository']
            _cascade_ids = []
            for _fk_id in data:
                _relation_ids = self.repository.fetch_by(
                        _relation_table,
                        [_pk],
                        {_fk: {'op': '=', 'value': _fk_id}},
                        {_fk: _fk_id}
                        )
                _cascade_ids += [x[0] for x in _relation_ids.fetchall()]
            soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
            _repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field = _pk)

        def many_to_many(**args):
            _relation_table = args['_relation_table']
            _relation_join_table = args['_relation_join_table']
            _pk = args['_pk']
            _relation_columns = args['_relation_columns']
            _repository = args['_repository']
            _cascade_ids = []
            for _fk_id in data:
                sql = create_select_join_soft_delete_filter(_relation_table, _pk,
                                                            _relation_join_table, _relation_columns)
                _relation_ids = self.repository.execute(sql, {'id': _fk_id})
                _cascade_ids += [x[0] for x in _relation_ids.fetchall()]
            soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
            _repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field = _pk)

        now = datetime.now().isoformat()
        soft_deletes = [{extension_field: now, id_field: x} for x in data]
        self.repository.update_batch(table_name, soft_deletes, where_field = id_field)

        self._walk_cascade_options(one_to_many = one_to_many, many_to_many = many_to_many)


class OnUpdateTimestampExtension(TableExtension):
    def set_field_data(self, form_data):
        _field = self.config['default_field']
        if _field not in form_data:
            form_data[_field] = datetime.now().isoformat()
        return form_data

    def unset_field_data(self, form_data):
        _field = self.config['default_field']
        del form_data[_field]
        return form_data


class OnCreateTimestampExtension(TableExtension):
    def set_columns(self, columns):
        _field = self.config['default_field']
        if _field not in columns:
            columns += [_field]
        return columns

    def set_field_data(self, params):
        _field = self.config['default_field']
        if _field not in params:
            params[_field] = datetime.now().isoformat()
        return params

    def unset_field_data(self, form_data):
        _field = self.config['default_field']
        del form_data[_field]
        return form_data


INTERNAL_EXTENSION_DEFAULTS = {
        'livecycle': {
                'soft_delete':         SoftDeleteExtension,
                'on_update_timestamp': OnUpdateTimestampExtension,
                'on_create_timestamp': OnCreateTimestampExtension
                }
        }
