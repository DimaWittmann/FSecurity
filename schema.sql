drop table if exists profile;
create table profile(
    profile_id integer primary key autoincrement,
    login varchar(20) not null,
    password varchar(20) not null
);


drop table if exists file;
create table file(
    file_id integer primary key autoincrement,
    profile_id integer,
    name varchar(20) not null,
    referens varchar(20) not null
);
