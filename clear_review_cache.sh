#!/bin/bash
# Clear only app review caches, preserve databases

cd "$(dirname "$0")/cache"

# Remove all app-specific cache directories (those with dots in name like com.app.id)
for dir in */; do
    if [[ "$dir" =~ \. ]]; then
        echo "Deleting $dir"
        rm -rf "$dir"
    fi
done

echo "Review caches cleared. Job history and other databases preserved."
