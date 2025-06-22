-- Create SCHEDULE database
CREATE DATABASE IF NOT EXISTS SCHEDULE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE SCHEDULE;

-- Employees table
CREATE TABLE IF NOT EXISTS Employees (
    EmployeeID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL,
    Phone VARCHAR(50) NOT NULL,
    Address VARCHAR(255),
    Picture LONGBLOB,
    Position VARCHAR(100),
    DateHired DATE,
    Notes TEXT,
    IsDefaultSender BOOLEAN DEFAULT 0,
    EmailPassword TEXT
);

-- Clients table
CREATE TABLE IF NOT EXISTS Clients (
    ClientID INT AUTO_INCREMENT PRIMARY KEY,
    ClientName VARCHAR(255) NOT NULL,
    Email VARCHAR(255) NOT NULL,
    Phone VARCHAR(50),
    Picture LONGBLOB,
    Address VARCHAR(255),
    Company VARCHAR(255),
    Notes TEXT,
    CleaningSuppliesNeeded TEXT,
    Comments TEXT,
    EmailQueuePrompt TEXT
);

-- ClientPictures table (gallery images for clients)
CREATE TABLE IF NOT EXISTS ClientPictures (
    PictureID INT AUTO_INCREMENT PRIMARY KEY,
    ClientID INT NOT NULL,
    FileName VARCHAR(255),
    Picture LONGBLOB,
    FOREIGN KEY (ClientID) REFERENCES Clients(ClientID) ON DELETE CASCADE
);

-- Events table
CREATE TABLE IF NOT EXISTS Events (
    EventID INT AUTO_INCREMENT PRIMARY KEY,
    EventName VARCHAR(255) NOT NULL,
    EventDate DATE NOT NULL,
    EventStartTime TIME NOT NULL,
    EventEndTime TIME NOT NULL,
    Description TEXT,
    EventColor VARCHAR(50),
    EmployeeID INT,
    ClientID INT,
    RecurringID INT,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
    FOREIGN KEY (ClientID) REFERENCES Clients(ClientID) ON DELETE CASCADE,
    FOREIGN KEY (RecurringID) REFERENCES RecurringEvents(RecurringID) ON DELETE SET NULL
);

-- RecurringEvents table
CREATE TABLE IF NOT EXISTS RecurringEvents (
    RecurringID INT AUTO_INCREMENT PRIMARY KEY,
    Pattern VARCHAR(50) NOT NULL, -- daily, weekly, biweekly, monthly, yearly
    `Interval` INT NOT NULL DEFAULT 1,
    StartDate DATE NOT NULL,
    EndDate DATE,
    EventName VARCHAR(255) NOT NULL,
    Description TEXT,
    EventColor VARCHAR(50),
    EmployeeID INT,
    ClientID INT,
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    FOREIGN KEY (ClientID) REFERENCES Clients(ClientID) ON DELETE CASCADE
);

-- Indexes for performance (optional)
CREATE INDEX idx_event_date ON Events(EventDate);
CREATE INDEX idx_client_email ON Clients(Email);
CREATE INDEX idx_employee_email ON Employees(Email);