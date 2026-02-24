"""
Data management utilities for loading and saving bot data
"""
import json
import os
from src.config import MEMBERS_DATA_FILE, GUILD_CONFIG_FILE


class DataManager:
    """Handles loading and saving of bot data"""
    
    @staticmethod
    def load_tracked_members():
        """Load tracked members from JSON file"""
        if os.path.exists(MEMBERS_DATA_FILE):
            try:
                with open(MEMBERS_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert string keys to integers
                    return {
                        int(guild_id): {
                            int(member_id): timestamp 
                            for member_id, timestamp in members.items()
                        }
                        for guild_id, members in data.items()
                    }
            except Exception as e:
                print(f"❌ Error loading member data: {e}")
                return {}
        return {}
    
    @staticmethod
    def load_guild_configs():
        """Load guild configurations from JSON file"""
        if os.path.exists(GUILD_CONFIG_FILE):
            try:
                with open(GUILD_CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert string keys to integers
                    return {
                        int(guild_id): config 
                        for guild_id, config in data.items()
                    }
            except Exception as e:
                print(f"❌ Error loading guild configs: {e}")
                return {}
        return {}
    
    @staticmethod
    def save_data(unverified_members, guild_configs):
        """Save both tracked members and guild configs"""
        try:
            # Save tracked members
            with open(MEMBERS_DATA_FILE, 'w') as f:
                json.dump(unverified_members, f, indent=4)
            
            # Save guild configurations
            with open(GUILD_CONFIG_FILE, 'w') as f:
                json.dump(guild_configs, f, indent=4)
                
            return True
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return False
