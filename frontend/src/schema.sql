-- ============================================================
--  Tasks Management App — PostgreSQL Migration Schema
--  Generated: 2026-06-21
-- ============================================================

-- Enable pgcrypto for gen_random_uuid() if not already active
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
--  USERS
--  Core authentication table. All other entities reference it.
-- ============================================================
CREATE TABLE users (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(50)   UNIQUE NOT NULL,
    email         VARCHAR(100)  UNIQUE NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    avatar_url    VARCHAR(255),
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  users               IS 'Registered user accounts';
COMMENT ON COLUMN users.password_hash IS 'bcrypt / argon2 hash — never store plaintext';
COMMENT ON COLUMN users.avatar_url    IS 'Optional profile picture URL';


-- ============================================================
--  TEAMS
--  Workspaces for collaborative task management.
-- ============================================================
CREATE TABLE teams (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_by  UUID         NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  teams            IS 'Collaborative workspaces';
COMMENT ON COLUMN teams.created_by IS 'User who created the team; becomes the initial owner';


-- ============================================================
--  TEAM MEMBERS
--  Many-to-many: users ↔ teams, with a role per membership.
-- ============================================================
CREATE TABLE team_members (
    id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id   UUID        NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id   UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role      VARCHAR(20) NOT NULL DEFAULT 'member'
                          CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- A user can only appear once per team
    CONSTRAINT uq_team_members_team_user UNIQUE (team_id, user_id)
);

COMMENT ON TABLE  team_members      IS 'Membership & role assignments within a team';
COMMENT ON COLUMN team_members.role IS 'owner | admin | member';


-- ============================================================
--  TASKS
--  Core work item. Supports AI extraction metadata and
--  optional photo attachment.
-- ============================================================
CREATE TABLE tasks (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text         TEXT        NOT NULL,
    priority     VARCHAR(20) NOT NULL DEFAULT 'normal'
                             CHECK (priority IN ('urgent', 'normal', 'low')),
    status       VARCHAR(20) NOT NULL DEFAULT 'open'
                             CHECK (status IN ('open', 'in_progress', 'done', 'cancelled')),
    deadline     TIMESTAMP,
    photo_url    VARCHAR(255),

    -- AI-specific fields
    ai_extracted      BOOLEAN   NOT NULL DEFAULT FALSE,
    ai_summary        TEXT,
    ai_suggested_tags TEXT[],

    created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  tasks                   IS 'Individual task items created by or for users';
COMMENT ON COLUMN tasks.priority          IS 'urgent | normal | low';
COMMENT ON COLUMN tasks.status            IS 'open | in_progress | done | cancelled';
COMMENT ON COLUMN tasks.ai_extracted      IS 'TRUE when the task was parsed/created by the AI pipeline';
COMMENT ON COLUMN tasks.ai_summary        IS 'Optional AI-generated summary of the task text';
COMMENT ON COLUMN tasks.ai_suggested_tags IS 'Array of tag strings suggested by the AI';


-- ============================================================
--  TASK SHARES
--  Publishes a task to a team so all members can see it.
-- ============================================================
CREATE TABLE task_shares (
    id        UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id   UUID      NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    team_id   UUID      NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    shared_by UUID      NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    shared_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- A task can only be shared to a given team once
    CONSTRAINT uq_task_shares_task_team UNIQUE (task_id, team_id)
);

COMMENT ON TABLE  task_shares           IS 'Links tasks to teams for collaborative visibility';
COMMENT ON COLUMN task_shares.shared_by IS 'User who performed the share action';


-- ============================================================
--  INDEXES — query-pattern driven
-- ============================================================

-- Tasks: most common filter is "all tasks owned by a user"
CREATE INDEX idx_tasks_user_id   ON tasks(user_id);

-- Tasks: priority queue view (urgent first)
CREATE INDEX idx_tasks_priority  ON tasks(priority);

-- Tasks: upcoming deadlines dashboard
CREATE INDEX idx_tasks_deadline  ON tasks(deadline)
    WHERE deadline IS NOT NULL;

-- Tasks: filter by status (open board, done archive, etc.)
CREATE INDEX idx_tasks_status    ON tasks(status);

-- Tasks: AI-extracted flag for analytics / review queue
CREATE INDEX idx_tasks_ai_extracted ON tasks(ai_extracted)
    WHERE ai_extracted = TRUE;

-- Team members: "which teams does this user belong to?"
CREATE INDEX idx_team_members_user_id ON team_members(user_id);

-- Team members: "who is in this team?"
CREATE INDEX idx_team_members_team_id ON team_members(team_id);

-- Task shares: "which teams have access to this task?"
CREATE INDEX idx_task_shares_task_id  ON task_shares(task_id);

-- Task shares: "all tasks shared with this team?"
CREATE INDEX idx_task_shares_team_id  ON task_shares(team_id);


-- ============================================================
--  AUTO-UPDATE updated_at TRIGGER
--  Keeps updated_at accurate without application-layer code.
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- ============================================================
--  SEED: default roles sanity-check (optional, remove in prod)
-- ============================================================
-- INSERT INTO users (username, email, password_hash)
-- VALUES ('admin', 'admin@example.com', '<hashed>');
