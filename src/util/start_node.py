from run_command import run_command

# Initialize the database
run_command("pipenv run init-db")

# Print message and start the server
print("Starting server...")
run_command("pipenv run python -m src.openleadr_node")
