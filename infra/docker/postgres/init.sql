-- SentinelOps seed data
INSERT INTO clusters (id, name, status, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'default',
  'active',
  NOW(),
  NOW()
) ON CONFLICT DO NOTHING;
