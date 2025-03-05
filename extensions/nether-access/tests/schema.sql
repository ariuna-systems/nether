-------------------------------------------------------------------------------
-- Account
-------------------------------------------------------------------------------
create table account
(
    id            uuid primary key,
    email         varchar unique           not null,
    name          varchar(255) unique      not null,
    password_hash varchar(255)             not null,
    created_at    timestamp with time zone not null default now(),
    updated_at    timestamp with time zone not null default now()
);
-------------------------------------------------------------------------------
create table role
(
    id         uuid primary key,
    name       varchar(255) unique      not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);
-------------------------------------------------------------------------------
create table account_role
(
    account_id uuid                     not null,
    role_id    uuid                     not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    primary key (account_id, role_id),
    foreign key (account_id) references account (id),
    foreign key (role_id) references role (id)
);
-------------------------------------------------------------------------------
create table account_session
(
    id         uuid primary key,
    account_id uuid                     not null,
    expires_at timestamp with time zone not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),

    foreign key (account_id) references account (id)
);
-------------------------------------------------------------------------------
create table account_secret
(
    account_id uuid primary key,
    secret     varchar(32)              not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),

    foreign key (account_id) references account (id)
);
-------------------------------------------------------------------------------
-- Item
-------------------------------------------------------------------------------
create table item
(
    id         uuid primary key,
    created_by uuid not null references account (id)
);
-------------------------------------------------------------------------------
-- Access control
-------------------------------------------------------------------------------
create table access_entry
(
    id         uuid default gen_random_uuid() primary key,
    account_id uuid references account (id) on delete cascade,
    role_id    uuid references role (id) on delete cascade,
    item_id    uuid not null references item (id) on delete cascade,
    unique (account_id, role_id, item_id),
    check ( -- Either account_id is set or role_id, not both, not none
        (account_id is not null and role_id is null) or
        (account_id is null and role_id is not null)
        )
);