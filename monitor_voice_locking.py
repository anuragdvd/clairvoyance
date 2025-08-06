#!/usr/bin/env python3
"""
Voice Locking Log Monitor

Real-time monitoring script to track voice locking system activity.
Shows key events like enrollment, speaker detection, and transcription filtering.
"""

import subprocess
import sys
import time
import re
from datetime import datetime

# Define log patterns to watch for
LOG_PATTERNS = {
    "🔊 INITIALIZATION": [
        "INITIALIZING VOICE LOCKING SYSTEM",
        "Voice locking enabled",
        "Speaker diarization service initialized",
        "VOICE LOCKING SYSTEM READY"
    ],
    "🎙️ ENROLLMENT": [
        "STARTING SPEAKER ENROLLMENT",
        "COMPLETING SPEAKER ENROLLMENT",
        "Speaker enrollment completed",
        "Speaker.*enrolled successfully",
        "TARGET SPEAKER DETECTED"
    ],
    "✅ ALLOWING": [
        "ALLOWING transcription",
        "allowing:",
        "Target speaker already enrolled"
    ],
    "🚫 FILTERING": [
        "FILTERING transcription",
        "Non-target speaker detected",
        "non_target_speaker"
    ],
    "🎵 AUDIO": [
        "Audio chunk ready",
        "Audio chunk processed",
        "Processing audio frame"
    ],
    "❌ ERRORS": [
        "Failed to initialize",
        "Error",
        "❌",
        "enrollment failed"
    ]
}

def colorize_log(line):
    """Add colors to log lines based on content"""
    colors = {
        "🔊": "\033[96m",    # Cyan
        "🎙️": "\033[93m",    # Yellow  
        "✅": "\033[92m",    # Green
        "🚫": "\033[91m",    # Red
        "🎵": "\033[94m",    # Blue
        "❌": "\033[91m",    # Red
        "🎯": "\033[95m",    # Magenta
        "⚠️": "\033[93m"     # Yellow
    }
    
    reset = "\033[0m"
    
    for emoji, color in colors.items():
        if emoji in line:
            return f"{color}{line}{reset}"
    
    return line

def get_log_category(line):
    """Categorize log line based on content"""
    for category, patterns in LOG_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return category
    return "OTHER"

def monitor_logs(log_file=None):
    """Monitor logs in real-time"""
    print("🎤 Voice Locking Log Monitor")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Monitoring voice locking activity...")
    print("=" * 50)
    
    if log_file:
        # Monitor specific log file
        cmd = ["tail", "-f", log_file]
    else:
        # Try to find application logs
        possible_logs = [
            "logs/app.log",
            "app.log", 
            "/var/log/clairvoyance.log"
        ]
        
        log_file_found = None
        for log_path in possible_logs:
            try:
                with open(log_path, 'r'):
                    log_file_found = log_path
                    break
            except FileNotFoundError:
                continue
        
        if log_file_found:
            print(f"📁 Monitoring log file: {log_file_found}")
            cmd = ["tail", "-f", log_file_found]
        else:
            print("📁 No log file found, monitoring stdout...")
            # Monitor the running application
            cmd = ["python", "app/main.py"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        stats = {
            "enrollments": 0,
            "allowed": 0,
            "filtered": 0,
            "errors": 0
        }
        
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            # Filter for voice locking related logs
            voice_keywords = [
                "voice", "speaker", "enrollment", "diarization", 
                "transcription", "🔊", "🎙️", "✅", "🚫", "🎵", "🎯"
            ]
            
            if any(keyword.lower() in line.lower() for keyword in voice_keywords):
                category = get_log_category(line)
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Update stats
                if "ENROLLMENT" in category:
                    stats["enrollments"] += 1
                elif "ALLOWING" in category:
                    stats["allowed"] += 1
                elif "FILTERING" in category:
                    stats["filtered"] += 1
                elif "ERROR" in category:
                    stats["errors"] += 1
                
                # Format and print log line
                colored_line = colorize_log(line)
                print(f"[{timestamp}] {category:15} {colored_line}")
                
                # Print stats summary periodically
                if (stats["allowed"] + stats["filtered"]) % 10 == 0 and stats["allowed"] + stats["filtered"] > 0:
                    print(f"\n📊 Stats: ✅ {stats['allowed']} allowed | 🚫 {stats['filtered']} filtered | 🎙️ {stats['enrollments']} enrollments | ❌ {stats['errors']} errors\n")
    
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        if process:
            process.terminate()
    except Exception as e:
        print(f"❌ Error monitoring logs: {e}")

def show_help():
    """Show help information"""
    print("""
🎤 Voice Locking Log Monitor - Help

Usage:
    python monitor_voice_locking.py [log_file]

Examples:
    python monitor_voice_locking.py                    # Auto-detect log file
    python monitor_voice_locking.py logs/app.log       # Monitor specific file
    python monitor_voice_locking.py --help             # Show this help

What to Look For:
    🔊 INITIALIZATION    - Voice locking system startup
    🎙️ ENROLLMENT        - Speaker enrollment process
    ✅ ALLOWING          - Transcriptions allowed through
    🚫 FILTERING         - Transcriptions filtered out
    🎵 AUDIO            - Audio processing events
    ❌ ERRORS           - Error conditions

Key Log Messages:
    ✅ "VOICE LOCKING SYSTEM READY" - System initialized
    🎙️ "STARTING SPEAKER ENROLLMENT" - Enrollment begun
    ✅ "Speaker enrollment completed" - Enrollment successful  
    🎯 "Voice locking is now ACTIVE" - Ready to filter
    ✅ "ALLOWING transcription: 'text'" - Text allowed
    🚫 "FILTERING transcription: 'text'" - Text filtered

Troubleshooting:
    - If no voice locking logs appear, check ENABLE_VOICE_LOCKING=true
    - If enrollment fails, check HUGGINGFACE_HUB_TOKEN is set
    - If no filtering occurs, check speaker similarity threshold
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "help"]:
            show_help()
            sys.exit(0)
        else:
            monitor_logs(sys.argv[1])
    else:
        monitor_logs()