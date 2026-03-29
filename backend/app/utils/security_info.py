"""
Security Information Collector for Financial Monitor
Robust system for collecting device, location, and time data
Works reliably regardless of user's network configuration
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
import pytz
import logging

logger = logging.getLogger(__name__)


class SecurityInfoCollector:
    """Collects and formats security information for email templates"""

    # Cache for public IP (to avoid multiple API calls)
    _cached_public_ip: Optional[str] = None
    _cache_timestamp: Optional[datetime] = None
    CACHE_DURATION_SECONDS = 300  # 5 minutes

    # macOS version names
    MACOS_VERSIONS = {
        "15": "Sequoia",
        "14": "Sonoma",
        "13": "Ventura",
        "12": "Monterey",
        "11": "Big Sur",
        "10.15": "Catalina",
        "10.14": "Mojave",
        "10.13": "High Sierra",
        "10.12": "Sierra",
    }

    # Known mobile device models
    DEVICE_MODELS = {
        # iPhone models
        r'iPhone16,2': 'iPhone 15 Pro Max',
        r'iPhone16,1': 'iPhone 15 Pro',
        r'iPhone15,5': 'iPhone 15 Plus',
        r'iPhone15,4': 'iPhone 15',
        r'iPhone15,3': 'iPhone 14 Pro Max',
        r'iPhone15,2': 'iPhone 14 Pro',
        r'iPhone14,8': 'iPhone 14 Plus',
        r'iPhone14,7': 'iPhone 14',
        r'iPhone14,3': 'iPhone 13 Pro Max',
        r'iPhone14,2': 'iPhone 13 Pro',
        r'iPhone14,5': 'iPhone 13',
        r'iPhone14,4': 'iPhone 13 Mini',
        # iPad models
        r'iPad14,6': 'iPad Pro 12.9" (6th gen)',
        r'iPad14,5': 'iPad Pro 11" (4th gen)',
        r'iPad13,19': 'iPad (10th gen)',
        r'iPad13,18': 'iPad (10th gen)',
        # Samsung models (from User-Agent)
        r'SM-S928': 'Samsung Galaxy S24 Ultra',
        r'SM-S926': 'Samsung Galaxy S24+',
        r'SM-S921': 'Samsung Galaxy S24',
        r'SM-S918': 'Samsung Galaxy S23 Ultra',
        r'SM-S916': 'Samsung Galaxy S23+',
        r'SM-S911': 'Samsung Galaxy S23',
        r'SM-G99': 'Samsung Galaxy S21',
        r'SM-A': 'Samsung Galaxy A Series',
        r'SM-N': 'Samsung Galaxy Note',
        r'SM-F': 'Samsung Galaxy Fold',
        r'SM-Z': 'Samsung Galaxy Z',
        # Xiaomi
        r'Redmi': 'Xiaomi Redmi',
        r'POCO': 'Xiaomi POCO',
        r'Mi \d+': 'Xiaomi Mi',
        # Huawei
        r'HUAWEI': 'Huawei',
        r'Honor': 'Honor',
        # Google Pixel
        r'Pixel 8 Pro': 'Google Pixel 8 Pro',
        r'Pixel 8': 'Google Pixel 8',
        r'Pixel 7': 'Google Pixel 7',
        r'Pixel 6': 'Google Pixel 6',
    }

    @staticmethod
    def parse_user_agent(user_agent: str) -> Dict[str, Any]:
        """
        Parse User-Agent string with detailed security information
        Returns comprehensive device, browser, and OS details
        """
        if not user_agent:
            return {
                "browser": "Unknown",
                "browser_version": "",
                "browser_engine": "Unknown",
                "os": "Unknown",
                "os_version": "",
                "os_arch": "",
                "device_type": "Unknown",
                "device_model": "",
                "device_vendor": "",
                "is_mobile": False,
                "is_bot": False,
                "raw": ""
            }

        result = {
            "raw": user_agent,
            "is_bot": False,
            "is_mobile": False
        }

        # Bot detection
        bot_patterns = [
            r'bot', r'crawl', r'spider', r'slurp', r'search',
            r'mediapartners', r'Googlebot', r'Bingbot', r'YandexBot'
        ]
        if any(re.search(p, user_agent, re.I) for p in bot_patterns):
            result["is_bot"] = True
            result["browser"] = "Bot/Crawler"
            result["browser_version"] = ""
            result["browser_engine"] = ""
            result["os"] = "Server"
            result["os_version"] = ""
            result["os_arch"] = ""
            result["device_type"] = "Bot"
            result["device_model"] = ""
            result["device_vendor"] = ""
            return result

        # ===== BROWSER DETECTION =====
        browser_patterns = [
            (r'Edg[eA]?/(\d+(?:\.\d+)*)', 'Microsoft Edge', 'Chromium'),
            (r'OPR/(\d+(?:\.\d+)*)', 'Opera', 'Chromium'),
            (r'Vivaldi/(\d+(?:\.\d+)*)', 'Vivaldi', 'Chromium'),
            (r'Brave', 'Brave', 'Chromium'),
            (r'YaBrowser/(\d+(?:\.\d+)*)', 'Yandex Browser', 'Chromium'),
            (r'SamsungBrowser/(\d+(?:\.\d+)*)', 'Samsung Internet', 'Chromium'),
            (r'UCBrowser/(\d+(?:\.\d+)*)', 'UC Browser', 'Chromium'),
            (r'Chrome/(\d+(?:\.\d+)*)', 'Google Chrome', 'Chromium'),
            (r'Firefox/(\d+(?:\.\d+)*)', 'Mozilla Firefox', 'Gecko'),
            (r'Version/(\d+(?:\.\d+)*).*Safari', 'Apple Safari', 'WebKit'),
            (r'MSIE\s(\d+(?:\.\d+)*)', 'Internet Explorer', 'Trident'),
            (r'Trident.*rv:(\d+(?:\.\d+)*)', 'Internet Explorer', 'Trident'),
        ]

        result["browser"] = "Unknown Browser"
        result["browser_version"] = ""
        result["browser_engine"] = "Unknown"

        for pattern, name, engine in browser_patterns:
            match = re.search(pattern, user_agent, re.I)
            if match:
                result["browser"] = name
                result["browser_engine"] = engine
                if match.lastindex:
                    result["browser_version"] = match.group(1)
                break

        # ===== OS DETECTION =====
        result["os"] = "Unknown OS"
        result["os_version"] = ""
        result["os_arch"] = ""

        # Windows detection with build number
        win_match = re.search(r'Windows NT (\d+\.\d+)(?:.*Build[/\s](\d+))?', user_agent, re.I)
        if win_match:
            nt_version = win_match.group(1)
            build = win_match.group(2) if win_match.lastindex >= 2 else None

            win_versions = {
                "10.0": "Windows 10",
                "6.3": "Windows 8.1",
                "6.2": "Windows 8",
                "6.1": "Windows 7",
                "6.0": "Windows Vista",
                "5.2": "Windows XP x64",
                "5.1": "Windows XP",
            }

            result["os"] = win_versions.get(nt_version, f"Windows NT {nt_version}")

            # Windows 11 detection (Build >= 22000)
            if nt_version == "10.0" and build:
                build_num = int(build)
                if build_num >= 22000:
                    result["os"] = "Windows 11"
                result["os_version"] = f"Build {build}"

            # Architecture
            if "Win64" in user_agent or "x64" in user_agent or "WOW64" in user_agent:
                result["os_arch"] = "64-bit"
            elif "Win32" in user_agent:
                result["os_arch"] = "32-bit"

        # macOS detection
        mac_match = re.search(r'Mac OS X (\d+)[._](\d+)(?:[._](\d+))?', user_agent, re.I)
        if mac_match:
            major = mac_match.group(1)
            minor = mac_match.group(2)
            patch = mac_match.group(3) or "0"

            version_key = major if int(major) >= 11 else f"{major}.{minor}"
            version_name = SecurityInfoCollector.MACOS_VERSIONS.get(version_key, "")

            if version_name:
                result["os"] = f"macOS {version_name}"
            else:
                result["os"] = "macOS"

            result["os_version"] = f"{major}.{minor}.{patch}"

            # Apple Silicon vs Intel
            if "ARM" in user_agent:
                result["os_arch"] = "Apple Silicon"
            else:
                result["os_arch"] = "Intel"

        # iOS detection
        ios_match = re.search(r'(?:iPhone|iPod).*OS (\d+)[._](\d+)', user_agent, re.I)
        if ios_match:
            result["os"] = "iOS"
            result["os_version"] = f"{ios_match.group(1)}.{ios_match.group(2)}"

        # iPadOS detection
        ipad_match = re.search(r'iPad.*OS (\d+)[._](\d+)', user_agent, re.I)
        if ipad_match:
            result["os"] = "iPadOS"
            result["os_version"] = f"{ipad_match.group(1)}.{ipad_match.group(2)}"

        # Android detection
        android_match = re.search(r'Android (\d+(?:\.\d+)*)', user_agent, re.I)
        if android_match:
            result["os"] = "Android"
            result["os_version"] = android_match.group(1)

        # Linux detection
        if "Linux" in user_agent and not android_match:
            if "Ubuntu" in user_agent:
                result["os"] = "Ubuntu Linux"
            elif "Fedora" in user_agent:
                result["os"] = "Fedora Linux"
            elif "Debian" in user_agent:
                result["os"] = "Debian Linux"
            else:
                result["os"] = "Linux"

            if "x86_64" in user_agent or "x64" in user_agent:
                result["os_arch"] = "64-bit"

        # Chrome OS
        if "CrOS" in user_agent:
            result["os"] = "Chrome OS"
            cros_match = re.search(r'CrOS\s+\w+\s+(\d+(?:\.\d+)*)', user_agent)
            if cros_match:
                result["os_version"] = cros_match.group(1)

        # ===== DEVICE DETECTION =====
        result["device_type"] = "Desktop"
        result["device_model"] = ""
        result["device_vendor"] = ""

        # Mobile detection
        if re.search(r'Mobile|Android.*Mobile|iPhone|iPod', user_agent, re.I):
            result["device_type"] = "Mobile"
            result["is_mobile"] = True
        elif re.search(r'Tablet|iPad|Android(?!.*Mobile)|PlayBook', user_agent, re.I):
            result["device_type"] = "Tablet"
            result["is_mobile"] = True
        elif re.search(r'TV|SmartTV|WebTV|GoogleTV|BRAVIA|AppleTV', user_agent, re.I):
            result["device_type"] = "Smart TV"
        elif re.search(r'Watch|WatchOS', user_agent, re.I):
            result["device_type"] = "Smartwatch"
        elif re.search(r'Xbox|PlayStation|Nintendo', user_agent, re.I):
            result["device_type"] = "Gaming Console"

        # Device model detection
        for pattern, model in SecurityInfoCollector.DEVICE_MODELS.items():
            if re.search(pattern, user_agent, re.I):
                result["device_model"] = model
                # Extract vendor
                if "iPhone" in model or "iPad" in model:
                    result["device_vendor"] = "Apple"
                elif "Samsung" in model:
                    result["device_vendor"] = "Samsung"
                elif "Xiaomi" in model or "Redmi" in model or "POCO" in model:
                    result["device_vendor"] = "Xiaomi"
                elif "Google" in model or "Pixel" in model:
                    result["device_vendor"] = "Google"
                elif "Huawei" in model:
                    result["device_vendor"] = "Huawei"
                elif "Honor" in model:
                    result["device_vendor"] = "Honor"
                break

        # Generic vendor detection if not found
        if not result["device_vendor"]:
            if "iPhone" in user_agent or "iPad" in user_agent or "Mac" in user_agent:
                result["device_vendor"] = "Apple"
            elif "Samsung" in user_agent:
                result["device_vendor"] = "Samsung"

        return result

    @staticmethod
    def format_device_string(user_agent: str, request=None) -> str:
        """
        Format device info with detailed security information
        Uses User-Agent Client Hints for accurate Windows 11 detection
        Example: "Microsoft Edge 144.0, Windows 11 Pro (64-bit) — Desktop"
        """
        info = SecurityInfoCollector.parse_user_agent(user_agent)

        # Check User-Agent Client Hints for accurate OS detection
        if request:
            info = SecurityInfoCollector._enhance_with_client_hints(info, request)

        # Browser string
        browser_str = info["browser"]
        if info["browser_version"]:
            # Shorten version to major.minor
            version_parts = info["browser_version"].split(".")[:2]
            browser_str += f" {'.'.join(version_parts)}"

        # OS string
        os_str = info["os"]
        if info.get("os_edition"):
            os_str += f" {info['os_edition']}"
        if info["os_version"] and info["os"] not in ["Windows 10", "Windows 11"]:
            os_str += f" {info['os_version']}"
        if info["os_arch"]:
            os_str += f" ({info['os_arch']})"

        # Device string
        device_str = info["device_type"]
        if info["device_model"]:
            device_str = info["device_model"]
        elif info["device_vendor"] and info["device_type"] != "Desktop":
            device_str = f"{info['device_vendor']} {info['device_type']}"

        return f"{browser_str}, {os_str} — {device_str}"

    @staticmethod
    def _enhance_with_client_hints(info: Dict[str, Any], request) -> Dict[str, Any]:
        """
        Enhance device info with User-Agent Client Hints headers
        These provide accurate Windows 11 detection
        """
        # Sec-CH-UA-Platform-Version gives Windows version
        platform_version = request.headers.get("Sec-CH-UA-Platform-Version", "").strip('"')
        platform = request.headers.get("Sec-CH-UA-Platform", "").strip('"')
        ua_mobile = request.headers.get("Sec-CH-UA-Mobile", "")
        ua_model = request.headers.get("Sec-CH-UA-Model", "").strip('"')
        ua_arch = request.headers.get("Sec-CH-UA-Arch", "").strip('"')
        ua_bitness = request.headers.get("Sec-CH-UA-Bitness", "").strip('"')

        # Windows 11 detection via platform version
        if platform.lower() == "windows" and platform_version:
            try:
                major_version = int(platform_version.split(".")[0])
                if major_version >= 13:  # Windows 11 reports as 13.0.0 or higher
                    info["os"] = "Windows 11"
                elif major_version >= 10:
                    info["os"] = "Windows 11"  # Version 10+ in Client Hints = Windows 11
                elif major_version >= 1:
                    info["os"] = "Windows 10"
            except (ValueError, IndexError):
                pass

        # macOS version from Client Hints
        if platform.lower() == "macos" and platform_version:
            try:
                parts = platform_version.split(".")
                major = parts[0]
                version_name = SecurityInfoCollector.MACOS_VERSIONS.get(major, "")
                if version_name:
                    info["os"] = f"macOS {version_name}"
                    info["os_version"] = platform_version
            except (ValueError, IndexError):
                pass

        # Architecture from Client Hints
        if ua_arch:
            if ua_arch.lower() in ["arm", "arm64"]:
                if "mac" in platform.lower():
                    info["os_arch"] = "Apple Silicon"
                else:
                    info["os_arch"] = "ARM"
            elif ua_arch.lower() in ["x86", "x64", "x86_64"]:
                if ua_bitness == "64":
                    info["os_arch"] = "64-bit"
                else:
                    info["os_arch"] = "32-bit"

        # Mobile detection from Client Hints
        if ua_mobile == "?1":
            info["is_mobile"] = True
            if info["device_type"] == "Desktop":
                info["device_type"] = "Mobile"

        # Device model from Client Hints
        if ua_model and not info["device_model"]:
            info["device_model"] = ua_model

        return info

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Check if IP is private/local"""
        if not ip:
            return True
        private_patterns = [
            r'^127\.',
            r'^10\.',
            r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'^192\.168\.',
            r'^::1$',
            r'^localhost$',
            r'^fe80:',
            r'^fc00:',
            r'^fd00:',
        ]
        return any(re.match(p, ip) for p in private_patterns)

    @staticmethod
    async def _get_public_ip_from_service() -> Optional[str]:
        """Get public IP from external services (multiple fallbacks)"""
        services = [
            ("https://api.ipify.org?format=json", "ip"),
            ("https://ipinfo.io/json", "ip"),
            ("https://api.ip.sb/ip", None),  # Returns plain text
            ("https://icanhazip.com", None),  # Returns plain text
        ]

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                for url, json_key in services:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            if json_key:
                                data = response.json()
                                ip = data.get(json_key, "").strip()
                            else:
                                ip = response.text.strip()

                            # Validate IP format
                            if ip and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                                return ip
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Failed to get public IP: {e}")

        return None

    @staticmethod
    async def get_real_ip(request) -> str:
        """
        Extract real client IP with robust detection
        Handles proxies, VPNs, Cloudflare, and local development
        """
        # Priority 1: Cloudflare
        cf_ip = request.headers.get("CF-Connecting-IP", "").strip()
        if cf_ip and not SecurityInfoCollector._is_private_ip(cf_ip):
            return cf_ip

        # Priority 2: True-Client-IP (Cloudflare Enterprise)
        true_client_ip = request.headers.get("True-Client-IP", "").strip()
        if true_client_ip and not SecurityInfoCollector._is_private_ip(true_client_ip):
            return true_client_ip

        # Priority 3: X-Real-IP (Nginx)
        real_ip = request.headers.get("X-Real-IP", "").strip()
        if real_ip and not SecurityInfoCollector._is_private_ip(real_ip):
            return real_ip

        # Priority 4: X-Forwarded-For (can contain chain of IPs)
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            # Parse the chain, find first non-private IP
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            for ip in ips:
                if ip and not SecurityInfoCollector._is_private_ip(ip):
                    return ip

        # Priority 5: Direct connection
        direct_ip = None
        if hasattr(request, 'client') and request.client:
            direct_ip = request.client.host

        # If we have a private IP, try to get public IP from external service
        if not direct_ip or SecurityInfoCollector._is_private_ip(direct_ip):
            # Check cache first
            now = datetime.now()
            if (SecurityInfoCollector._cached_public_ip and
                SecurityInfoCollector._cache_timestamp and
                (now - SecurityInfoCollector._cache_timestamp).seconds < SecurityInfoCollector.CACHE_DURATION_SECONDS):
                return SecurityInfoCollector._cached_public_ip

            # Get from external service
            public_ip = await SecurityInfoCollector._get_public_ip_from_service()
            if public_ip:
                SecurityInfoCollector._cached_public_ip = public_ip
                SecurityInfoCollector._cache_timestamp = now
                return public_ip

        return direct_ip or "Unknown"

    @staticmethod
    async def get_location_by_ip(ip: str) -> Dict[str, str]:
        """
        Get location by IP using multiple services with fallbacks
        Returns: {"city": "Almaty", "country": "Kazakhstan", "country_code": "KZ"}
        """
        if not ip or ip == "Unknown" or SecurityInfoCollector._is_private_ip(ip):
            return {
                "city": "Unknown",
                "country": "Unknown",
                "country_code": "",
                "region": ""
            }

        services = [
            {
                "url": f"http://ip-api.com/json/{ip}?fields=status,city,country,countryCode,regionName",
                "parser": lambda d: {
                    "city": d.get("city", "Unknown"),
                    "country": d.get("country", "Unknown"),
                    "country_code": d.get("countryCode", ""),
                    "region": d.get("regionName", "")
                } if d.get("status") == "success" else None
            },
            {
                "url": f"https://ipinfo.io/{ip}/json",
                "parser": lambda d: {
                    "city": d.get("city", "Unknown"),
                    "country": d.get("country", "Unknown"),
                    "country_code": d.get("country", ""),
                    "region": d.get("region", "")
                } if "city" in d else None
            },
        ]

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                for service in services:
                    try:
                        response = await client.get(service["url"])
                        if response.status_code == 200:
                            data = response.json()
                            result = service["parser"](data)
                            if result and result["city"] != "Unknown":
                                return result
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Failed to get location for IP {ip}: {e}")

        return {
            "city": "Unknown",
            "country": "Unknown",
            "country_code": "",
            "region": ""
        }

    @staticmethod
    def format_time(timezone: str = "Asia/Almaty") -> str:
        """
        Format current time as: "Month Day, Year at HH:MM (GMT+Z)"
        Example: "February 09, 2026 at 05:30 (GMT+5)"
        """
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)

            # Get UTC offset
            offset = now.strftime('%z')  # e.g., +0500
            offset_hours = int(offset[:3])  # e.g., +5

            # Format offset string
            if offset_hours >= 0:
                gmt_str = f"GMT+{offset_hours}"
            else:
                gmt_str = f"GMT{offset_hours}"

            # Format date/time
            formatted = now.strftime("%B %d, %Y at %H:%M")
            return f"{formatted} ({gmt_str})"
        except Exception:
            return datetime.now().strftime("%B %d, %Y at %H:%M")

    @staticmethod
    async def collect_security_info(
        request,
        user_name: str,
        code: str,
        timezone: str = "Asia/Almaty"
    ) -> Dict[str, Any]:
        """
        Collect all security information for email template
        Returns JSON object ready for template rendering
        """
        user_agent = request.headers.get("User-Agent", "")

        # Get real IP (handles localhost, VPN, proxy, etc.)
        client_ip = await SecurityInfoCollector.get_real_ip(request)

        # Get location data
        location = await SecurityInfoCollector.get_location_by_ip(client_ip)

        # Format location display string
        if location["city"] != "Unknown" and location["country_code"]:
            location_display = f"{location['city']}, {location['country_code']}"
        else:
            location_display = client_ip

        return {
            "user": {
                "name": user_name,
                "display_name": user_name if user_name else "User"
            },
            "code": {
                "raw": code,
                "formatted": f"{code[:3]}-{code[3:]}" if len(code) == 6 else code,
                "spaced": ' '.join(code) if code else ""
            },
            "device": {
                "raw_user_agent": user_agent,
                "formatted": SecurityInfoCollector.format_device_string(user_agent, request),
                **SecurityInfoCollector.parse_user_agent(user_agent)
            },
            "location": {
                "ip": client_ip,
                "city": location["city"],
                "country": location["country"],
                "country_code": location["country_code"],
                "display": location_display
            },
            "time": {
                "formatted": SecurityInfoCollector.format_time(timezone),
                "timezone": timezone,
                "timestamp": datetime.now(pytz.timezone(timezone)).isoformat()
            }
        }


# Convenience function for quick usage
async def get_security_data(request, user_name: str, code: str) -> Dict[str, Any]:
    """Quick helper to get all security data"""
    return await SecurityInfoCollector.collect_security_info(request, user_name, code)
