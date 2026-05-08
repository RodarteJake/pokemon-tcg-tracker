"""Set or reset a user's password.

Usage:
    python -m scripts.set_user_password --user <username>
    python -m scripts.set_user_password               # prompts for username
"""
import argparse
import getpass
import sys

from auth import hash_password
from db import get_connection


SENTINEL_HASH = "!"


def main():
    parser = argparse.ArgumentParser(description="Set or reset a user's password.")
    parser.add_argument("--user", help="Username (will prompt if not provided)")
    args = parser.parse_args()
    # 2. If no username provided, prompt for it
    username = args.user
    if not username:
        username = input("Username: ").strip()
        if not username:
            print("Username cannot be empty.")
            sys.exit(1)
    # 3. Look up user in DB; error if not found
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, hashed_password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row is None:
        print("ERROR: User not found", file=sys.stderr)
        sys.exit(1)
    # 4. If existing hash is not the sentinel, require confirmation
    #    (re-type username to confirm)
    existing_hash = row["hashed_password"]
    if existing_hash != SENTINEL_HASH:
        print(f"User '{username}' already has a password set.")
        confirm = input(f"To confirm resetting the password, please re-type the username: ").strip()
        if confirm != username:
            print("Confirmation did not match. Aborting.")
            sys.exit(1)
    # 5. Prompt for password twice (using getpass), error if mismatch
    password = getpass.getpass("New password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)
    # 6. Hash and UPDATE the database
    new_hash = hash_password(password)        
    user_id = row["user_id"]
    with conn:          
        conn.execute("UPDATE users SET hashed_password = ? WHERE user_id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()
    # 7. Print success
    print(f"Password for user '{username}' has been updated.")

if __name__ == "__main__":
    main()