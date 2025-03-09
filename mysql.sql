CREATE TABLE IF NOT EXISTS EMP_LEAVES (
    empfirname VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    leaves_left INT NOT NULL,
    PRIMARY KEY (empfirname, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


INSERT INTO EMP_LEAVES (empfirname, year, leaves_left) VALUES
('John', 2025, 12),
('Alice', 2025, 8),
('Bob', 2025, 20),
('Rahul', 2025, 15); 

select * from EMP_LEAVES el 