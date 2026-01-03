-- Creator Support AI Database Schema for Supabase

-- Creators table
CREATE TABLE IF NOT EXISTS creators (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    credits_remaining INTEGER DEFAULT 100,
    subscription_tier TEXT DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content uploads table
CREATE TABLE IF NOT EXISTS content_uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size INTEGER,
    processing_status TEXT DEFAULT 'pending',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    student_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    sources JSONB,
    should_escalate BOOLEAN DEFAULT FALSE,
    reviewed BOOLEAN DEFAULT FALSE,
    feedback_rating INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_conversations_creator_id ON conversations(creator_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_uploads_creator_id ON content_uploads(creator_id);
CREATE INDEX IF NOT EXISTS idx_should_escalate ON conversations(should_escalate) WHERE should_escalate = TRUE;

-- Enable Row Level Security
ALTER TABLE creators ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- RLS Policies for creators
CREATE POLICY "Creators can view own data" ON creators
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Creators can update own data" ON creators
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for content_uploads
CREATE POLICY "Creators can view own uploads" ON content_uploads
    FOR SELECT USING (creator_id = auth.uid());

CREATE POLICY "Creators can insert own uploads" ON content_uploads
    FOR INSERT WITH CHECK (creator_id = auth.uid());

-- RLS Policies for conversations
CREATE POLICY "Creators can view own conversations" ON conversations
    FOR SELECT USING (creator_id = auth.uid());

CREATE POLICY "Creators can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (creator_id = auth.uid());

CREATE POLICY "Creators can update own conversations" ON conversations
    FOR UPDATE USING (creator_id = auth.uid());
