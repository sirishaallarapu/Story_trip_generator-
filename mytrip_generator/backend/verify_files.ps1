$basePath = "C:\Users\Dell\Desktop\mytrip_generator\mytrip_generator\backend"
$files = @(
    "models\itinerary.py",
    "agents\itinerary_builder.py",
    "routes\trip_routes.py",
    "tools\prompt_templates.py"
)
foreach ($file in $files) {
    $fullPath = Join-Path $basePath $file
    if (Test-Path $fullPath) {
        Write-Host "Found: $fullPath"
        Get-Content $fullPath -First 10
        # Check for JSON enforcement
        if ($file -eq "agents\itinerary_builder.py") {
            $content = Get-Content $fullPath -Raw
            if ($content -match 'response_format=\{"type": "json_object"\}') {
                Write-Host "JSON enforcement found in $file"
            } else {
                Write-Host "WARNING: JSON enforcement missing in $file"
            }
        }
    } else {
        Write-Host "Missing: $fullPath"
    }
}
# Test OpenAI API connectivity
$envPath = Join-Path $basePath ".env"
if (Test-Path $envPath) {
    Write-Host "Found .env file"
    Get-Content $envPath
} else {
    Write-Host "Missing .env file"
}