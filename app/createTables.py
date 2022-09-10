from db import conn 



commands = (
        """
        CREATE TABLE newcases (
		id SERIAL PRIMARY KEY, 
		m_name VARCHAR(255) NOT NULL, 
		mobile VARCHAR(10) NOT NULL, 
		date VARCHAR(255) NOT NULL, 
		age INTEGER NOT NULL, 
		file VARCHAR(255) NOT NULL, 
		location VARCHAR(255) NOT NULL);

        """
        ,
        """
        CREATE TABLE police 
		(id SERIAL PRIMARY KEY, 
		police_id INTEGER NOT NULL, 
		p_name VARCHAR(20) NOT NULL, 
		station VARCHAR(20) NOT NULL, 
		post VARCHAR(20) NOT NULL, 
		mobile VARCHAR(10) NOT NULL, 
		password VARCHAR(255) NOT NULL);

        """
        ,

        """
        CREATE TABLE spoted 
		(id SERIAL PRIMARY KEY, 
		image VARCHAR(255) NOT NULL, 
		location VARCHAR(255) NOT NULL, 
		name VARCHAR(255) NOT NULL,
		date VARCHAR(255) NOT NULL);

        """
        ,

        """
        CREATE TABLE users 
		(id SERIAL PRIMARY KEY, 
		name VARCHAR(255) NOT NULL, 
		mobile VARCHAR(255) NOT NULL, 
		location VARCHAR(255) NOT NULL, 
		file VARCHAR(255) NOT NULL);

        """

        )
cur = conn.cursor()
        # create table one by one
for command in commands:
    cur.execute(command)

        
conn.commit()
print('Tables created succesfully')      

