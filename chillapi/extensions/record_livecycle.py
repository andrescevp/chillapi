from datetime import datetime

from chillapi.abc import TableExtension
from chillapi.database.query_builder import create_select_join_soft_delete_filter


class SoftDeleteExtension(TableExtension):
    def add_query_filter(self, query: dict, query_values: dict):
        _field = self.config['default_field']
        query = {**query, **{_field: {'op': 'isnull', 'value': None}}}
        query_values = {**query_values, **{_field: None}}

        return query, query_values

    def soft_delete(self, id_field_where, id, extension_field, response):
        now = datetime.now().isoformat()
        _field = self.config['default_field']
        self.repository.update_record(
            self.table,
            id_field_where,
            id,
            {id_field_where: id, _field: now}
        )
        response.response['message'] = 'ok'
        response.response['code'] = 200

        if 'cascade' in self.config:
            _cascades = self.config['cascade']
            if 'one_to_many' in _cascades:
                _one_to_many = _cascades['one_to_many']
                for _otm, _relation in enumerate(_one_to_many):
                    _relation_table = _relation['table']
                    _pk = _relation['column_id']
                    _fk = _relation['column_fk']
                    _relation_ids = self.repository.fetch_by(
                        _relation_table,
                        [_pk],
                        {_fk: {'op': '=', 'value': id}},
                        {_fk: id}
                    )
                    _cascade_ids = [x[0] for x in _relation_ids.fetchall()]
                    soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                    self.repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)
            if 'many_to_many' in _cascades:
                _one_to_many = _cascades['many_to_many']
                for _otm, _relation in enumerate(_one_to_many):
                    _relation_table = _relation['table']
                    _relation_join_table = _relation['join_table']
                    _pk = _relation['column_id']
                    _relation_columns = _relation['join_columns']
                    _relation_column_id = _relation['column_id']
                    sql = create_select_join_soft_delete_filter(_relation_table, _relation_column_id,
                                                                _relation_join_table, _relation_columns)
                    _relation_ids = self.repository.execute(sql, {'id': id})
                    _cascade_ids = [x[0] for x in _relation_ids.fetchall()]
                    soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                    self.repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)

    def soft_delete_batch(self, table_name, extension_field, id_field, data):
        now = datetime.now().isoformat()
        soft_deletes = [{extension_field: now, id_field: x} for x in data]
        self.repository.update_batch(table_name, soft_deletes, where_field=id_field)

        if 'cascade' in self.config:
            _cascades = self.config['cascade']
            if 'one_to_many' in _cascades:
                _one_to_many = _cascades['one_to_many']
                for _otm, _relation in enumerate(_one_to_many):
                    _relation_table = _relation['table']
                    _pk = _relation['column_id']
                    _fk = _relation['column_fk']
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
                    self.repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)
            if 'many_to_many' in _cascades:
                _one_to_many = _cascades['many_to_many']
                for _otm, _relation in enumerate(_one_to_many):
                    _relation_table = _relation['table']
                    _relation_join_table = _relation['join_table']
                    _pk = _relation['column_id']
                    _relation_columns = _relation['join_columns']
                    _relation_column_id = _relation['column_id']
                    _cascade_ids = []
                    for _fk_id in data:
                        sql = create_select_join_soft_delete_filter(_relation_table, _relation_column_id,
                                                                    _relation_join_table, _relation_columns)
                        _relation_ids = self.repository.execute(sql, {'id': _fk_id})
                        _cascade_ids += [x[0] for x in _relation_ids.fetchall()]
                    soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                    self.repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)

    def remove_filter_field_from_dict(self, dictionary: dict, soft_delete_field):
        del dictionary[soft_delete_field]
        return dictionary


class OnUpdateTimestampExtension(TableExtension):
    def set_field_data(self, form_data):
        _field = self.config['default_field']
        if _field not in form_data:
            form_data[_field] = datetime.now().isoformat()

    def unset_field_data(self, form_data):
        _field = self.config['default_field']
        del form_data[_field]


class OnCreateTimestampExtension(TableExtension):
    def set_columns(self, columns):
        _field = self.config['default_field']
        if _field not in columns:
            columns += [_field]

    def set_field_data(self, params):
        _field = self.config['default_field']
        if _field not in params:
            params[_field] = datetime.now().isoformat()

    def unset_field_data(self, form_data):
        _field = self.config['default_field']
        del form_data[_field]


INTERNAL_EXTENSION_DEFAULTS = {
    'livecycle': {
        'soft_delete': SoftDeleteExtension,
        'on_update_timestamp': OnUpdateTimestampExtension,
        'on_create_timestamp': OnCreateTimestampExtension
    }
}
