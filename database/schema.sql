-- Database schema for AI Job Application Copilot

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    linkedin TEXT,
    github TEXT,
    job_description TEXT,
    resume_filename TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
