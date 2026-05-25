"""
LLM Brain - Groq API Integration (ENHANCED)
============================================
Handles all AI conversation logic and API communication
Now with: Weather, News, Reminders, System Control
"""

from groq import Groq
from typing import List, Dict, Optional
import config
import re

# Import enhanced modules
from weather import get_weather, format_weather_report, format_weather_speech

# Import camera system (try simple first for better reliability)
try:
    from camera_simple import start_camera_surveillance, stop_camera_surveillance, get_camera_status
    CAMERA_MODULE = "simple"
except ImportError:
    try:
        from surveillance_enhanced import start_camera_surveillance, stop_camera_surveillance, get_camera_status
        CAMERA_MODULE = "enhanced"
    except ImportError:
        from surveillance import start_camera_surveillance, stop_camera_surveillance, get_camera_status
        CAMERA_MODULE = "original"

# Import other surveillance functions
from surveillance import (
    open_app, open_website, search_web, get_system_info, 
    format_system_report, get_surveillance_system
)

from reminder import (
    set_reminder, list_reminders, delete_reminder, 
    format_reminders_list, get_reminder_system
)
from news import (
    get_headlines, get_tech_news, get_world_news, search_news,
    format_headlines, format_headlines_speech
)

# Import image generator + file explorer
from image_generator import (
    select_file, select_files, select_folder,
    open_explorer, get_file_explorer,
    detect_image_generation_request, handle_image_generation,
)

# Import WhatsApp Integration (ENHANCED!)
from whatsapp_integration import (
    detect_whatsapp_command,
    execute_whatsapp_command,
    get_whatsapp,
    wa_send, wa_chat, wa_add_contact, wa_contacts, wa_templates
)

print(f"[LLM] Using camera module: {CAMERA_MODULE}")


class LLMBrain:
    """
    Manages conversation with Groq LLM API + Enhanced Features
    
    Responsibilities:
    - API communication
    - Conversation history management
    - Context window management
    - Command detection and routing
    - Integration with surveillance, reminders, news
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the LLM brain
        
        Args:
            api_key: Groq API key
        """
        self.api_key = api_key
        self.client: Optional[Groq] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.is_connected = False
        
        # Try to initialize client
        if api_key and api_key != "your_groq_api_key_here":
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Groq client"""
        try:
            self.client = Groq(api_key=self.api_key)
            self.is_connected = True
            print("[LLM] Groq client initialized successfully")
        except Exception as e:
            print(f"[LLM ERROR] Failed to initialize Groq client: {e}")
            self.is_connected = False
            raise
    
    def add_user_message(self, message: str):
        """
        Add user message to conversation history
        
        Args:
            message: User's message text
        """
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self._trim_history()
    
    def add_assistant_message(self, message: str):
        """
        Add assistant message to conversation history
        
        Args:
            message: Assistant's response text
        """
        self.conversation_history.append({
            "role": "assistant",
            "content": message
        })
        self._trim_history()
    
    def _trim_history(self):
        """
        Trim conversation history to prevent context overflow
        
        Keeps only the most recent messages as defined in config.
        """
        max_history = config.MAX_CONVERSATION_HISTORY
        if len(self.conversation_history) > max_history:
            # Keep the most recent messages
            self.conversation_history = self.conversation_history[-max_history:]
            print(f"[LLM] Trimmed history to {max_history} messages")
    
    # ====================================================================
    # COMMAND DETECTION METHODS
    # ====================================================================
    
    def _detect_weather_request(self, message: str) -> Optional[str]:
        """
        Detect if user is asking about weather and extract location
        
        Args:
            message: User's message
            
        Returns:
            Location name if weather request detected, None otherwise
        """
        message_lower = message.lower()
        
        # Weather keywords
        weather_keywords = [
            'weather', 'temperature', 'forecast', 'hot', 'cold',
            'raining', 'rain', 'sunny', 'cloudy', 'snow', 'snowing'
        ]
        
        # Check if message contains weather keywords
        has_weather_keyword = any(keyword in message_lower for keyword in weather_keywords)
        
        if not has_weather_keyword:
            return None
        
        # Extract location using common patterns
        # Pattern 1: "weather in [location]"
        match = re.search(r'(?:weather|temperature|forecast).*?(?:in|at|for)\s+([a-zA-Z\s]+?)(?:\?|$|today|tomorrow)', message_lower)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "what's the weather in [location]"
        match = re.search(r"what'?s?\s+(?:the\s+)?(?:weather|temperature).*?(?:in|at)\s+([a-zA-Z\s]+?)(?:\?|$)", message_lower)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: "[location] weather"
        match = re.search(r'([a-zA-Z\s]+?)\s+(?:weather|temperature|forecast)', message_lower)
        if match:
            location = match.group(1).strip()
            # Exclude common words that aren't locations
            exclude_words = ['the', 'what', 'how', 'is', 'today', 'tomorrow', 'current']
            if location not in exclude_words:
                return location
        
        return None
    
    def _detect_app_launch(self, message: str) -> Optional[str]:
        """Detect app launch command"""
        message_lower = message.lower()
        
        patterns = [
            r'open\s+(.+?)(?:\s+app|\s+application|$)',
            r'launch\s+(.+?)(?:\s+app|\s+application|$)',
            r'start\s+(.+?)(?:\s+app|\s+application|$)',
            r'run\s+(.+?)(?:\s+app|\s+application|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _detect_website_open(self, message: str) -> Optional[str]:
        """Detect website opening command"""
        message_lower = message.lower()
        
        patterns = [
            r'open\s+(?:website\s+)?(.+\.(?:com|org|net|io|co|in))',
            r'go\s+to\s+(.+\.(?:com|org|net|io|co|in))',
            r'visit\s+(.+\.(?:com|org|net|io|co|in))',
            r'browse\s+(?:to\s+)?(.+\.(?:com|org|net|io|co|in))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _detect_web_search(self, message: str) -> Optional[Dict[str, str]]:
        """Detect web search command"""
        message_lower = message.lower()
        
        patterns = [
            r'search\s+(?:for\s+)?(.+?)(?:\s+on\s+(.+?))?$',
            r'google\s+(.+?)$',
            r'look\s+up\s+(.+?)$',
            r'find\s+(.+?)(?:\s+on\s+(.+?))?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                query = match.group(1).strip()
                engine = match.group(2).strip() if match.lastindex == 2 else 'google'
                return {'query': query, 'engine': engine}
        
        return None
    
    def _detect_reminder_set(self, message: str) -> Optional[Dict[str, str]]:
        """Detect reminder setting command"""
        message_lower = message.lower()
        
        patterns = [
            r'remind\s+me\s+(?:to\s+)?(.+?)\s+(?:in|at|on)\s+(.+?)$',
            r'set\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+?)\s+(?:in|at|for)\s+(.+?)$',
            r'reminder:\s*(.+?)\s+(?:in|at)\s+(.+?)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return {
                    'message': match.group(1).strip(),
                    'when': match.group(2).strip()
                }
        
        return None
    
    def _detect_reminder_list(self, message: str) -> bool:
        """Detect reminder listing command"""
        message_lower = message.lower()
        
        patterns = [
            r'show\s+(?:my\s+)?reminders',
            r'list\s+(?:my\s+)?reminders',
            r'what\s+are\s+my\s+reminders',
            r'any\s+reminders',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    def _detect_news_request(self, message: str) -> Optional[Dict[str, str]]:
        """Detect news request"""
        message_lower = message.lower()
        
        # Check for news keywords
        if 'news' not in message_lower and 'headlines' not in message_lower:
            return None
        
        # Detect category
        if any(word in message_lower for word in ['tech', 'technology']):
            return {'type': 'tech'}
        elif any(word in message_lower for word in ['world', 'international']):
            return {'type': 'world'}
        elif any(word in message_lower for word in ['business', 'finance', 'economy']):
            return {'type': 'business'}
        else:
            return {'type': 'general'}
    
    def _detect_system_info(self, message: str) -> bool:
        """Detect system information request"""
        message_lower = message.lower()
        
        patterns = [
            r'system\s+info',
            r'computer\s+info',
            r'system\s+status',
            r'how\s+is\s+(?:my\s+)?(?:system|computer)',
            r'cpu\s+usage',
            r'memory\s+usage',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    def _detect_camera_start(self, message: str) -> bool:
        """Detect camera surveillance start command"""
        message_lower = message.lower()
        
        patterns = [
            r'start\s+camera',
            r'enable\s+camera',
            r'turn\s+on\s+camera',
            r'start\s+surveillance',
            r'start\s+monitoring',
            r'watch\s+for\s+motion',
            r'detect\s+motion',
            r'open\s+camera',
            r'activate\s+camera',
            r'camera\s+on',
            r'begin\s+surveillance',
            r'show\s+camera',
            r'start\s+cam',
            r'open\s+cam',
            r'activate\s+surveillance',
            r'open\s+surveillance',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    def _detect_camera_stop(self, message: str) -> bool:
        """Detect camera surveillance stop command"""
        message_lower = message.lower()
        
        patterns = [
            r'stop\s+camera',
            r'disable\s+camera',
            r'turn\s+off\s+camera',
            r'stop\s+surveillance',
            r'stop\s+monitoring',
            r'close\s+camera',
            r'camera\s+off',
            r'end\s+surveillance',
            r'deactivate\s+camera',
            r'stop\s+cam',
            r'close\s+cam',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    def _detect_camera_status(self, message: str) -> bool:
        """Detect camera status request"""
        message_lower = message.lower()
        
        patterns = [
            r'camera\s+status',
            r'surveillance\s+status',
            r'is\s+camera\s+on',
            r'monitoring\s+status',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    def _detect_file_analysis(self, message: str) -> bool:
        """Detect file analysis request"""
        message_lower = message.lower()
        
        patterns = [
            r'analyze\s+(?:a\s+)?file',
            r'analyze\s+(?:this\s+)?file',
            r'check\s+(?:a\s+)?file',
            r'examine\s+(?:a\s+)?file',
            r'open\s+file\s+(?:explorer|dialog)',
            r'select\s+(?:a\s+)?file',
            r'choose\s+(?:a\s+)?file',
            r'show\s+me\s+(?:a\s+)?file',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    def _detect_whatsapp_message(self, message: str) -> Optional[Dict]:
        """Detect WhatsApp commands using enhanced integration"""
        return detect_whatsapp_command(message)
    
    def _detect_open_explorer(self, message: str) -> bool:
        """Detect file explorer opening request"""
        message_lower = message.lower()
        
        patterns = [
            r'open\s+(?:file\s+)?explorer',
            r'open\s+(?:my\s+)?files',
            r'open\s+folder',
            r'browse\s+files',
            r'show\s+(?:file\s+)?explorer',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in patterns)
    
    # ====================================================================
    # COMMAND EXECUTION METHODS
    # ====================================================================
    
    def _execute_weather_request(self, location: str) -> str:
        """Execute weather request"""
        print(f"[LLM] Weather request for: {location}")
        weather_info = get_weather(location)
        
        if weather_info:
            return format_weather_report(weather_info)
        else:
            return f"I couldn't fetch the weather data for {location}. Please check the location name and try again."
    
    def _execute_app_launch(self, app_name: str) -> str:
        """Execute app launch"""
        print(f"[LLM] Launching app: {app_name}")
        result = open_app(app_name)
        return result['message']
    
    def _execute_website_open(self, url: str) -> str:
        """Execute website opening"""
        print(f"[LLM] Opening website: {url}")
        result = open_website(url)
        return result['message']
    
    def _execute_web_search(self, search_info: Dict[str, str]) -> str:
        """Execute web search"""
        print(f"[LLM] Searching: {search_info['query']}")
        result = search_web(search_info['query'], search_info['engine'])
        return f"I've opened a search for '{search_info['query']}' in your browser."
    
    def _execute_reminder_set(self, reminder_info: Dict[str, str]) -> str:
        """Execute reminder setting"""
        print(f"[LLM] Setting reminder: {reminder_info}")
        result = set_reminder(reminder_info['message'], reminder_info['when'])
        return result['message']
    
    def _execute_reminder_list(self) -> str:
        """Execute reminder listing"""
        print("[LLM] Listing reminders")
        reminders = list_reminders()
        return format_reminders_list(reminders)
    
    def _execute_news_request(self, news_type: str) -> str:
        """Execute news request"""
        print(f"[LLM] Fetching {news_type} news")
        
        if news_type == 'tech':
            headlines = get_tech_news(5)
        elif news_type == 'world':
            headlines = get_world_news(5)
        elif news_type == 'business':
            headlines = get_headlines('bbc', 'business', 5)
        else:
            headlines = get_world_news(5)
        
        return format_headlines(headlines)
    
    def _execute_system_info(self) -> str:
        """Execute system info request"""
        print("[LLM] Getting system info")
        info = get_system_info()
        return format_system_report(info)
    
    def _execute_camera_start(self) -> str:
        """Execute camera surveillance start"""
        print("[LLM] Starting camera surveillance")
        result = start_camera_surveillance()
        return result['message']
    
    def _execute_camera_stop(self) -> str:
        """Execute camera surveillance stop"""
        print("[LLM] Stopping camera surveillance")
        result = stop_camera_surveillance()
        return result['message']
    
    def _execute_camera_status(self) -> str:
        """Execute camera status request"""
        print("[LLM] Getting camera status")
        status = get_camera_status()
        
        if status['is_monitoring']:
            return f"Camera surveillance is ACTIVE. Motion events detected: {status['motion_count']}"
        else:
            return "Camera surveillance is currently INACTIVE."
    
    def _execute_file_analysis(self) -> str:
        """Execute file analysis"""
        print("[LLM] Opening file selection dialog")
        
        # Open file dialog
        file_path = select_file("Select a file to analyze")
        
        if not file_path:
            return "No file selected. Analysis cancelled."
        
        # Get file info
        info = get_file_explorer().get_file_info(file_path)
        
        if 'error' in info:
            return f"Error: {info['error']}"
        
        # Build response
        response = f"📁 File Analysis:\n\n"
        response += f"Name: {info['name']}\n"
        response += f"Path: {info['path']}\n"
        response += f"Size: {info['size_mb']:.2f} MB ({info['size']:,} bytes)\n"
        response += f"Type: {info['extension']}\n"
        response += f"Modified: {info['modified']}\n"
        response += f"Created: {info['created']}\n\n"
        
        # Analyze based on file type
        ext = info['extension'].lower()
        
        if ext in ['.txt', '.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.json', '.xml', '.md']:
            # Text file - read and analyze
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                lines = content.splitlines()
                response += f"📄 Text File Analysis:\n"
                response += f"Lines: {len(lines)}\n"
                response += f"Characters: {len(content)}\n"
                response += f"Words: {len(content.split())}\n\n"
                
                if ext == '.py':
                    # Python specific
                    imports = [l for l in lines if 'import' in l]
                    functions = [l for l in lines if l.strip().startswith('def ')]
                    classes = [l for l in lines if l.strip().startswith('class ')]
                    response += f"🐍 Python Specifics:\n"
                    response += f"Imports: {len(imports)}\n"
                    response += f"Functions: {len(functions)}\n"
                    response += f"Classes: {len(classes)}\n\n"
                
                # Show preview
                preview = content[:300]
                response += f"Preview (first 300 chars):\n{preview}..."
                
            except Exception as e:
                response += f"Could not read file contents: {e}"
        
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            response += "🖼️ Image file detected.\n"
            response += "Image analysis features available!"
        
        elif ext in ['.pdf']:
            response += "📄 PDF document detected.\n"
            response += "PDF analysis features available!"
        
        elif ext in ['.doc', '.docx']:
            response += "📝 Word document detected.\n"
            response += "Document analysis features available!"
        
        elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
            response += "🎬 Video file detected."
        
        elif ext in ['.mp3', '.wav', '.flac', '.ogg']:
            response += "🎵 Audio file detected."
        
        else:
            response += f"File type: {ext}\n"
            response += "Binary or unknown file type."
        
        return response
    
    def _execute_whatsapp_message(self, whatsapp_info: Dict) -> str:
        """Execute WhatsApp commands using enhanced integration"""
        wa = get_whatsapp()
        return execute_whatsapp_command(whatsapp_info, wa)
    
    def _execute_open_explorer(self) -> str:
        """Execute file explorer opening"""
        print("[LLM] Opening file explorer")
        
        folder = select_folder("Select a folder to open")
        
        if folder:
            open_explorer(folder)
            return f"📂 Opened File Explorer at:\n{folder}"
        else:
            return "No folder selected."
    
    # ====================================================================
    # MAIN RESPONSE METHOD
    # ====================================================================
    
    def get_response(self, user_message: str) -> str:
        """
        Get AI response for user message (with command detection)
        
        Args:
            user_message: The user's input text
            
        Returns:
            The AI's response text
            
        Raises:
            Exception: If API call fails or client not initialized
        """
        if not self.is_connected or not self.client:
            raise Exception("LLM client not connected. Please check your API key.")
        
        # ===== COMMAND DETECTION & EXECUTION =====
        
        # 1. Check for weather request
        location = self._detect_weather_request(user_message)
        if location:
            response = self._execute_weather_request(location)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 2. Check for app launch
        app_name = self._detect_app_launch(user_message)
        if app_name:
            response = self._execute_app_launch(app_name)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 3. Check for website opening
        website = self._detect_website_open(user_message)
        if website:
            response = self._execute_website_open(website)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 4. Check for web search
        search_info = self._detect_web_search(user_message)
        if search_info:
            response = self._execute_web_search(search_info)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 5. Check for reminder setting
        reminder_info = self._detect_reminder_set(user_message)
        if reminder_info:
            response = self._execute_reminder_set(reminder_info)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 6. Check for reminder list
        if self._detect_reminder_list(user_message):
            response = self._execute_reminder_list()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 7. Check for news request
        news_info = self._detect_news_request(user_message)
        if news_info:
            response = self._execute_news_request(news_info['type'])
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 8. Check for system info
        if self._detect_system_info(user_message):
            response = self._execute_system_info()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 9. Check for camera surveillance start
        if self._detect_camera_start(user_message):
            response = self._execute_camera_start()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 10. Check for camera surveillance stop
        if self._detect_camera_stop(user_message):
            response = self._execute_camera_stop()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 11. Check for camera status
        if self._detect_camera_status(user_message):
            response = self._execute_camera_status()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 12. Check for file analysis
        if self._detect_file_analysis(user_message):
            response = self._execute_file_analysis()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 13. Check for WhatsApp message
        whatsapp_info = self._detect_whatsapp_message(user_message)
        if whatsapp_info:
            response = self._execute_whatsapp_message(whatsapp_info)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response
        
        # 14. Check for file explorer opening
        if self._detect_open_explorer(user_message):
            response = self._execute_open_explorer()
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response

        # 15. Check for image generation request
        if detect_image_generation_request(user_message):
            print("[LLM] Image generation request detected")
            response = handle_image_generation(user_message)
            self.add_user_message(user_message)
            self.add_assistant_message(response)
            return response

        # ===== NORMAL LLM RESPONSE =====
        
        # Add user message to history
        self.add_user_message(user_message)
        
        # Build messages for API call
        messages = [
            {
                "role": "system",
                "content": config.SYSTEM_PROMPT
            }
        ] + self.conversation_history
        
        try:
            print(f"[LLM] Sending request to Groq API...")
            print(f"[LLM] User: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
            
            # Make API call
            completion = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
            )

            if not completion or not completion.choices:
                raise Exception("Empty response from Groq API")

            response = completion.choices[0].message.content.strip()
            
            print(f"[LLM] Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            
            # Add to history
            self.add_assistant_message(response)
            
            return response
            
        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            print(f"[LLM ERROR] {error_msg}")
            raise Exception(error_msg)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("[LLM] Conversation history cleared")
    
    def get_history_summary(self) -> str:
        """
        Get a summary of conversation history
        
        Returns:
            String with message count and preview
        """
        count = len(self.conversation_history)
        if count == 0:
            return "No conversation history"
        
        last_msg = self.conversation_history[-1]
        preview = last_msg['content'][:50] + "..." if len(last_msg['content']) > 50 else last_msg['content']
        
        return f"{count} messages in history. Last: {preview}"