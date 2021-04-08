select c.name as book_name, cr.*
from book c
         inner join book_category cr ON cr.id = c.book_category_id AND c.name = :name
