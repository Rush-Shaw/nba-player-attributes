import kagglehub

# Download latest version
path = kagglehub.dataset_download("willyiamyu/nba-2k-ratings-with-real-nba-stats")

print("Path to dataset files:", path)