CREATE TABLE files (
    file_id        BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    path           VARCHAR(1000) NOT NULL UNIQUE,
    filename       VARCHAR(255) NOT NULL,
    mime_type      VARCHAR(100),
    file_size      BIGINT,
    content_hash   CHAR(64),
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chunks (
    chunk_id       BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    file_id        BIGINT NOT NULL,
    chunk_index    INT NOT NULL,
    content        TEXT NOT NULL,
    start_offset   INT,
    end_offset     INT,

    CONSTRAINT fk_chunk_file
        FOREIGN KEY (file_id) REFERENCES files(file_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_file_chunk
        UNIQUE (file_id, chunk_index)
);

CREATE TABLE terms (
    term_id        BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    term           VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE chunk_terms (
    chunk_id       BIGINT NOT NULL,
    term_id        BIGINT NOT NULL,

    -- useful for ranking
    term_frequency INT NOT NULL DEFAULT 1,

    PRIMARY KEY (chunk_id, term_id),

    FOREIGN KEY (chunk_id)
        REFERENCES chunks(chunk_id)
        ON DELETE CASCADE,

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id)
        ON DELETE CASCADE
);
