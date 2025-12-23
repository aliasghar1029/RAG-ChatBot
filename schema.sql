-- Neon Postgres schema for chat history and related data

-- Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

-- User Queries table
CREATE TABLE IF NOT EXISTS user_queries (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(session_id),
    content TEXT NOT NULL,
    selected_text TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    context_chunks TEXT[] -- Array of chunk IDs used for this query
);

-- Responses table
CREATE TABLE IF NOT EXISTS responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES user_queries(query_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    source_chunks TEXT[], -- Array of chunk IDs used to generate the response
    confidence_score DECIMAL(3, 2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    token_count INTEGER
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_queries_session_id ON user_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_user_queries_timestamp ON user_queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_responses_query_id ON responses(query_id);
CREATE INDEX IF NOT EXISTS idx_responses_timestamp ON responses(timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at);