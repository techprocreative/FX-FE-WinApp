# Supabase Configuration Guide

## Production URLs

### Frontend
- **Domain**: https://fx.nusanexus.com
- **API Endpoint**: https://fx.nusanexus.com/api

### Supabase Settings

#### 1. Authentication Settings
Navigate to: **Authentication > URL Configuration**

**Site URL**: `https://fx.nusanexus.com`

**Redirect URLs** (add all):
```
https://fx.nusanexus.com
https://fx.nusanexus.com/auth/callback
https://fx.nusanexus.com/dashboard
http://localhost:3000
http://localhost:3000/auth/callback
http://localhost:3000/dashboard
```

#### 2. Storage Bucket Setup

Create bucket for ML models:

**Bucket Name**: `ml-models`
**Public**: `false` (private)
**File Size Limit**: 100 MB
**Allowed MIME types**: `application/octet-stream`

**Bucket Policies**:
```sql
-- Users can upload their own models
CREATE POLICY "Users can upload their own models"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'ml-models' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can view their own models
CREATE POLICY "Users can view their own models"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'ml-models' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can update their own models
CREATE POLICY "Users can update their own models"
    ON storage.objects FOR UPDATE
    USING (
        bucket_id = 'ml-models' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can delete their own models
CREATE POLICY "Users can delete their own models"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'ml-models' 
        AND auth.uid()::text = (storage.foldername(name))[1]
    );
```

#### 3. CORS Settings

Navigate to: **Settings > API**

Add to **CORS allowed origins**:
```
https://fx.nusanexus.com
http://localhost:3000
```

#### 4. Email Templates

Navigate to: **Authentication > Email Templates**

Update all email templates to use:
- **Site URL**: `https://fx.nusanexus.com`
- **Redirect URL**: `https://fx.nusanexus.com/auth/callback`

#### 5. Run Migration

Execute migration `002_ml_models.sql`:

```bash
# Via Supabase CLI
supabase db push

# Or via SQL Editor in Supabase Dashboard
# Copy and paste contents of supabase/migrations/002_ml_models.sql
```

#### 6. Verify Setup

**Check Tables**:
```sql
SELECT * FROM ml_models LIMIT 1;
```

**Check Storage Bucket**:
```sql
SELECT * FROM storage.buckets WHERE id = 'ml-models';
```

**Check Policies**:
```sql
SELECT * FROM storage.policies WHERE bucket_id = 'ml-models';
```

## Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key

# LLM Configuration
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_PROVIDER=openrouter
```

### Connector (config.yaml)
```yaml
supabase:
  url: "your_supabase_url"
  anon_key: "your_anon_key"

api:
  url: "https://fx.nusanexus.com"
```

## Testing Checklist

- [ ] User can register and login
- [ ] User can access dashboard
- [ ] User can generate strategy with AI
- [ ] Model training syncs to Supabase
- [ ] Model appears in ml_models table
- [ ] Model file uploaded to Storage
- [ ] User can download model on different device
- [ ] Auto-trading works with synced models
