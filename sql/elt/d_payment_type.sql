SELECT payment_type AS payment_type_code,
       CASE payment_type WHEN 'credit_card' THEN 'Credit Card' WHEN 'debit_card' THEN 'Debit Card'
            WHEN 'boleto' THEN 'Boleto' WHEN 'voucher' THEN 'Voucher'
            WHEN 'not_defined' THEN 'Not Defined' ELSE payment_type END AS payment_type_name,
       CASE WHEN payment_type IN ('credit_card','debit_card') THEN 'Card'
            WHEN payment_type = 'boleto'  THEN 'Boleto'
            WHEN payment_type = 'voucher' THEN 'Voucher'
            ELSE 'Other' END AS payment_method_group
FROM (SELECT DISTINCT payment_type FROM {sdl}.ORDER_PAYMENTS)
