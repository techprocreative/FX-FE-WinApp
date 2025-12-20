-- ============================================
-- Storage Bucket Setup for ML Models
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Create the ml-models bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'ml-models',
    'ml-models',
    false,  -- Private bucket
    104857600,  -- 100 MB limit
    ARRAY['application/octet-stream']::text[]
)
ON CONFLICT (id) DO NOTHING;

-- 2. Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 3. Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can upload their own models" ON storage.objects;
DROP POLICY IF EXISTS "Users can view their own models" ON storage.objects;
DROP POLICY IF EXISTS "Users can update their own models" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete their own models" ON storage.objects;

-- 4. Create storage policies for ml-models bucket

-- Allow users to upload to their own folder
CREATE POLICY "Users can upload their own models"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to view their own models
CREATE POLICY "Users can view their own models"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to update their own models
CREATE POLICY "Users can update their own models"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to delete their own models
CREATE POLICY "Users can delete their own models"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- 5. Verify bucket creation
SELECT 
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types,
    created_at
FROM storage.buckets 
WHERE id = 'ml-models';

-- 6. Verify policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies 
WHERE tablename = 'objects' 
AND policyname LIKE '%models%'
ORDER BY policyname;

-- ============================================
-- Expected Output:
-- - Bucket 'ml-models' created
-- - 4 policies created for storage.objects
-- ============================================
