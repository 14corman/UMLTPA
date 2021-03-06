/* This file is sourced during the initialization
 * of the crawler. Make sure everything is CREATE
 * IF NOT EXISTS, otherwise there will be errors
 */

CREATE TABLE IF NOT EXISTS task (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    manager_params TEXT NOT NULL,
    openwpm_version TEXT NOT NULL,
    browser_version TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS crawl (
    crawl_id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    browser_params TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES task(task_id));

CREATE TABLE IF NOT EXISTS xpath (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    xpath VARCHAR(500) NOT NULL,
    absolute_xpath VARCHAR(500),
    ctime DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, url));

CREATE TABLE IF NOT EXISTS site_visits (
    visit_id INTEGER PRIMARY KEY,
    crawl_id INTEGER NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

CREATE TABLE IF NOT EXISTS flash_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    domain VARCHAR(500),
    filename VARCHAR(500),
    local_path VARCHAR(1000),
    key TEXT,
    content TEXT,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id),
    FOREIGN KEY(visit_id) REFERENCES site_visits(id));

CREATE TABLE IF NOT EXISTS profile_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    baseDomain TEXT,
    name TEXT,
    value TEXT,
    host TEXT,
    path TEXT,
    expiry INTEGER,
    lastAccessed INTEGER,
    creationTime INTEGER,
    isSecure INTEGER,
    isHttpOnly INTEGER,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id),
    FOREIGN KEY(visit_id) REFERENCES site_visits(id));

CREATE TABLE IF NOT EXISTS localStorage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    page_url VARCHAR(500) NOT NULL,
    scope TEXT,
    KEY TEXT,
    value TEXT,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

/* Crawl History table */
CREATE TABLE IF NOT EXISTS crawl_history (
    crawl_id INTEGER,
    command TEXT,
    arguments TEXT,
    bool_success INTEGER,
    dtg DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

CREATE TABLE IF NOT EXISTS url_depth(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    depth INTEGER NOT NULL,
	url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS http_requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    top_level_url TEXT,
    method TEXT NOT NULL,
    referrer TEXT NOT NULL,
    headers TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    is_XHR BOOLEAN,
    is_frame_load BOOLEAN,
    is_full_page BOOLEAN,
    is_third_party_channel BOOLEAN,
    is_third_party_to_top_window BOOLEAN,
    triggering_origin TEXT,
    loading_origin TEXT,
    loading_href TEXT,
    req_call_stack TEXT,
    content_policy_type INTEGER NOT NULL,
    post_body TEXT,
    time_stamp TEXT NOT NULL,
	depth INTEGER,
	main INTEGER,
	A_one BOOLEAN,
	A_two BOOLEAN,
	B_one BOOLEAN,
	B_two BOOLEAN,
	C_one BOOLEAN,
	C_two BOOLEAN,
	D_one BOOLEAN,
	D_two BOOLEAN,
	E BOOLEAN,
	F_iframe REAL,
	F_script REAL,
	F_resource REAL,
	current_list BOOLEAN,
	two_month_list BOOLEAN,
	four_month_list BOOLEAN,
	six_month_list BOOLEAN,
	knn_pred BOOLEAN,
	nn_pred BOOLEAN
);

CREATE TABLE IF NOT EXISTS http_responses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    method TEXT NOT NULL,
    referrer TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    response_status_text TEXT NOT NULL,
    is_cached BOOLEAN NOT NULL,
    headers TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    location TEXT NOT NULL,
    time_stamp TEXT NOT NULL,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS http_redirects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    old_channel_id TEXT,
    new_channel_id TEXT,
    is_temporary BOOLEAN NOT NULL,
    is_permanent BOOLEAN NOT NULL,
    is_internal BOOLEAN NOT NULL,
    is_sts_upgrade BOOLEAN NOT NULL,
    time_stamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS javascript(
    id INTEGER PRIMARY KEY,
    crawl_id INTEGER,
    visit_id INTEGER,
    script_url TEXT,
    script_line TEXT,
    script_col TEXT,
    func_name TEXT,
    script_loc_eval TEXT,
    document_url TEXT,
    top_level_url TEXT,
    call_stack TEXT,
    symbol TEXT,
    operation TEXT,
    value TEXT,
    arguments TEXT,
    time_stamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS javascript_cookies(
    id INTEGER PRIMARY KEY ASC,
    crawl_id INTEGER,
    visit_id INTEGER,
    change TEXT,
    creationTime DATETIME,
    expiry DATETIME,
    is_http_only INTEGER,
    is_session INTEGER,
    last_accessed DATETIME,
    raw_host TEXT,
    expires INTEGER,
    host TEXT,
    is_domain INTEGER,
    is_secure INTEGER,
    name TEXT,
    path TEXT,
    policy INTEGER,
    status INTEGER,
    value TEXT
);
