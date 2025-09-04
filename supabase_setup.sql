-- Supabase SQL script to work with existing routes table
-- Run this in your Supabase SQL Editor

-- Your existing routes table structure (from screenshot):
-- id (int4), route_name (varchar), driver_id (int), start_location (varchar), end_location (varchar), created_at (timestamp)

-- Add additional columns for route optimization if they don't exist
ALTER TABLE routes ADD COLUMN IF NOT EXISTS total_distance_km DECIMAL(10,2);
ALTER TABLE routes ADD COLUMN IF NOT EXISTS total_time_minutes INTEGER;
ALTER TABLE routes ADD COLUMN IF NOT EXISTS total_orders INTEGER;
ALTER TABLE routes ADD COLUMN IF NOT EXISTS route_data JSONB;
ALTER TABLE routes ADD COLUMN IF NOT EXISTS optimization_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE routes ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(255);
ALTER TABLE routes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create indexes for better performance if they don't exist
CREATE INDEX IF NOT EXISTS idx_routes_driver_id ON routes(driver_id);
CREATE INDEX IF NOT EXISTS idx_routes_vehicle_id ON routes(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_routes_created_at ON routes(created_at);
CREATE INDEX IF NOT EXISTS idx_routes_optimization_status ON routes(optimization_status);

-- Enable Row Level Security (RLS)
ALTER TABLE optimized_routes ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations for authenticated users
-- Adjust this based on your security requirements
CREATE POLICY "Allow all operations for authenticated users" ON optimized_routes
    FOR ALL 
    TO authenticated 
    USING (true)
    WITH CHECK (true);

-- Create a policy to allow read access for anonymous users (optional)
CREATE POLICY "Allow read access for anonymous users" ON optimized_routes
    FOR SELECT 
    TO anon 
    USING (true);

-- Update the updated_at column automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_optimized_routes_updated_at 
    BEFORE UPDATE ON optimized_routes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a view for route summaries
CREATE OR REPLACE VIEW route_summaries AS
SELECT 
    route_id,
    vehicle_id,
    total_distance_km,
    total_time_minutes,
    total_orders,
    status,
    created_at
FROM optimized_routes
ORDER BY created_at DESC;
