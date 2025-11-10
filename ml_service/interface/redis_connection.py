import redis
import requests
import json
 
 
class RedisConnection:
    """Singleton class to manage a single Redis connection."""
    _instance = None
    _redis_client = None
 
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisConnection, cls).__new__(cls)
        return cls._instance
 
    def get_client(self, host="192.168.99.99", port=6379):
        """Get or create Redis client."""
        if self._redis_client is None:
            print(f"Creating new Redis connection to {host}:{port}...")
            self._redis_client = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self._redis_client.ping()
            print("Redis connection established!")
        return self._redis_client
 
    def close(self):
        """Close the Redis connection."""
        if self._redis_client is not None:
            self._redis_client.close()
            self._redis_client = None
            print("Redis connection closed.")
 
 
# Global singleton instance
_redis_connection = RedisConnection()
 
 
def send_result_to_dashboard(robot_name, data):
    """
    Send result data to dashboard by storing in Redis and posting to HTTP endpoint.
 
    Args:
        robot_name (str): The name of the robot/arm (used as Redis key and armLabel)
        data (dict): Dictionary containing the data to store in Redis
 
    Returns:
        dict: Status information with 'redis_success' and 'http_success' keys
 
    Raises:
        redis.ConnectionError: If cannot connect to Redis
        requests.RequestException: If HTTP request fails
    """
    redis_host = "192.168.99.99"
    redis_port = 6379
    http_url = "http://192.168.99.99:8080/collective/results"
 
    result = {
        'redis_success': False,
        'http_success': False
    }
 
    # Use singleton Redis connection
    try:
        r = _redis_connection.get_client(host=redis_host, port=redis_port)
 
        # Store data as JSON string
        data_json = json.dumps(data)
        r.set(robot_name, data_json)
        print(f"Stored in Redis: {robot_name} = {data_json}")
 
        result['redis_success'] = True
 
    except redis.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
        raise
    except Exception as e:
        print(f"Error with Redis operation: {e}")
        raise
 
    # Send HTTP POST request
    try:
        payload = {
            "armLabel": robot_name,
            "success": True
        }
 
        print(f"\nSending POST request to {http_url}...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
 
        response = requests.post(http_url, json=payload, timeout=5)
 
        print(f"Response status: {response.status_code}")
        if response.text:
            print(f"Response body: {response.text}")
 
        if response.status_code == 200:
            print("HTTP POST request successful!")
            result['http_success'] = True
        else:
            print(f"HTTP POST returned status code: {response.status_code}")
 
    except requests.ConnectionError as e:
        print(f"Error connecting to HTTP server: {e}")
        raise
    except requests.Timeout as e:
        print(f"HTTP request timed out: {e}")
        raise
    except Exception as e:
        print(f"Error with HTTP request: {e}")
        raise
 
    print("\nAll operations completed successfully!")
    return result
 
 
def close_redis_connection():
    """Close the singleton Redis connection. Call this when done with all operations."""
    _redis_connection.close()
 
