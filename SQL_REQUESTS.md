# SQL Requests for easy retrieval from DB without application

## SQL for retrieve contest for each user by client_code
~~~SQL
SELECT 
      u.client_code, u.name as client_name, u.status client_status, u.age, u.city,
      p.name as product_name, p.description as product_description, cr.rank as top_level, cr.potential_benefit, cr.recommendation_reason,
      pb.calculation_details
FROM clients u
LEFT JOIN client_recommendations cr ON u.client_code = cr.client_code
LEFT JOIN products p ON cr.product_id = p.id
LEFT JOIN product_benefits pb ON pb.client_code = u.client_code AND pb.product_id = p.id
WHERE u.client_code = [CLIENT_CODE] // put here client code
ORDER BY u.client_code, cr.rank
;
~~~
