-- Use the correct database
USE studentdbms;

-- --------------------------------------------------------
-- Table: User (for authentication)
-- User table
CREATE TABLE IF NOT EXISTS user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50),
  email VARCHAR(100) UNIQUE,
  password VARCHAR(1000)
);

-- Item table
CREATE TABLE IF NOT EXISTS item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT,
    name VARCHAR(100),
    category VARCHAR(100),
    description TEXT,
    `condition` VARCHAR(50),
    next_available_date DATE,
    current_rental_id INT,
    quantity INT,
    price FLOAT,
    availability ENUM('available', 'unavailable') DEFAULT 'available',
    mode ENUM('rent', 'sale', 'share') NOT NULL,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Rent table
CREATE TABLE IF NOT EXISTS rent (
  id INT AUTO_INCREMENT PRIMARY KEY,
  item_id INT,
  renter_id INT,
  rent_start_date DATE NOT NULL,
  rent_end_date DATE NOT NULL,
  rent_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  quantity INT,
  total_price FLOAT,
  status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
  FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY (renter_id) REFERENCES user(id) ON DELETE CASCADE,
  CHECK (rent_end_date >= rent_start_date)
);

-- Sale table
CREATE TABLE IF NOT EXISTS sale (
  id INT AUTO_INCREMENT PRIMARY KEY,
  item_id INT,
  buyer_id INT,
  quantity INT,
  sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  total_price FLOAT,
  status ENUM('completed', 'cancelled') DEFAULT 'completed',
  FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY (buyer_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Share table
CREATE TABLE IF NOT EXISTS share (
  id INT AUTO_INCREMENT PRIMARY KEY,
  item_id INT,
  borrower_id INT,
  share_start DATETIME,
  share_end DATETIME,
  quantity INT,
  notes TEXT,
  status ENUM('ongoing', 'returned') DEFAULT 'ongoing',
  FOREIGN KEY (item_id) REFERENCES item(id) ON DELETE CASCADE,
  FOREIGN KEY (borrower_id) REFERENCES user(id) ON DELETE CASCADE
);