-- ============================================
-- Storage Policies for ML Models Bucket
-- 
-- PREREQUISITE: Create bucket via Supabase Dashboard first!
-- 
-- Steps:
-- 1. Go to: Storage → New Bucket
-- 2. Bucket name: ml-models
-- 3. Public: OFF (private)
-- 4. File size limit: 100 MB
-- 5. Allowed MIME types: application/octet-stream
-- 6. Click "Create bucket"
-- 
-- Then run this SQL script to create policies
-- ============================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can upload their own models" ON storage.objects;
DROP POLICY IF EXISTS "Users can view their own models" ON storage.objects;
DROP POLICY IF EXISTS "Users can update their own models" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete their own models" ON storage.objects;

-- Create storage policies for ml-models bucket

-- Policy 1: Allow users to upload to their own folder
CREATE POLICY "Users can upload their own models"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy 2: Allow users to view their own models
CREATE POLICY "Users can view their own models"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy 3: Allow users to update their own models
CREATE POLICY "Users can update their own models"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy 4: Allow users to delete their own models
CREATE POLICY "Users can delete their own models"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'ml-models' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Verify policies were created
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    cmd
FROM pg_policies 
WHERE tablename = 'objects' 
AND policyname LIKE '%models%'
ORDER BY policyname;

-- ============================================
-- Expected Output: 4 policies listed
-- ============================================
