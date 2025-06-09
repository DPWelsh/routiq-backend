-- Update organization_members table to accept Clerk role format
-- This script updates the role constraint to accept Clerk's role values

-- Drop the existing role constraint
ALTER TABLE organization_members DROP CONSTRAINT IF EXISTS organization_members_role_check;

-- Add new constraint with Clerk role values
ALTER TABLE organization_members ADD CONSTRAINT organization_members_role_check 
CHECK (
    role IN (
        'org:owner',
        'org:admin', 
        'org:member',
        'org:viewer',
        -- Keep backward compatibility with simple roles
        'owner',
        'admin',
        'member', 
        'viewer'
    )
);

-- Update the default value to use Clerk format
ALTER TABLE organization_members ALTER COLUMN role SET DEFAULT 'org:member';

-- Optional: Update existing simple roles to Clerk format (uncomment if needed)
-- UPDATE organization_members SET role = 'org:' || role WHERE role NOT LIKE 'org:%';

COMMENT ON COLUMN organization_members.role IS 'Member role using Clerk format (org:owner, org:admin, org:member, org:viewer)'; 