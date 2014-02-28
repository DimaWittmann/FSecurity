drop table if exists profile;
create table profile(
    profile_id integer primary key autoincrement,
    login varchar(20) not null,
    password varchar(20) not null,
    email varchar not null,
    question varchar,
    answer varchar
);


drop table if exists file;
create table file(
    file_id integer primary key autoincrement,
    profile_id integer,
    title varchar not null,
    reference varchar not null
);

drop table if exists log;
create table log(
	log_id integer primary key autoincrement,
	profile_id integer,
	description varchar,
	warning_level integer,
    data integer
);

