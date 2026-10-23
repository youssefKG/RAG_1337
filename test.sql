create table if not exists STUDENT(id int primary key, first_name varchar(255) UNIQUE, last_name varchar(250));
CREATE TABLE SUBJET (id int PRIMARY KEY, name varchar(255));
CREATE TABLE NOTE(id int PRIMARY KEY, value int, subject_id int, student_id int, CONSTRAINT fk_student FOREIGN KEY (student_id) REFERENCES (STUDENT(id)), CONSTRAINT fk_subject FOREIGN key (subject_id) REFERENCES(SUBJECT(id)));
