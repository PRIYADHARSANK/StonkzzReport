#!/usr/bin/env python3
"""
Automated PDF Report Generator using Playwright
Automates browser interaction to generate PDF from the StonkzzReport website
"""

import os
import sys
import time
import subprocess
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

# Load environment variables from backend/.env
# Assuming this script is at the root of the project
backend_env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(backend_env_path)

# Make sure we can import from backend.scripts
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

class PDFReportGenerator:
    """Automates PDF generation from the StonkzzReport website"""
    
    def __init__(self, url="http://localhost:5173", download_dir=None):
        self.url = url
        self.download_dir = download_dir or os.path.join(os.getcwd(), "generated_reports")
        self.server_process = None
        self.pdf_path = None
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
    
    def _is_port_in_use(self, port=5173):
        """Check if a port is already in use (tries both IPv4 and IPv6)"""
        import socket
        
        # Try IPv4
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        
        # Try IPv6
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('::1', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        
        return False
    
    def _find_npm(self):
        """Find npm executable on the system"""
        # Try shutil.which first
        npm_path = shutil.which('npm')
        if npm_path:
            return npm_path
        
        # Try common Windows locations
        possible_paths = [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            os.path.expandvars(r"%APPDATA%\npm\npm.cmd"),
            os.path.expandvars(r"%ProgramFiles%\nodejs\npm.cmd"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _kill_existing_server(self, port=5173):
        """Kill any existing process using the port"""
        try:
            # Unix-like kill (Mac/Linux)
            if os.name != 'nt':
                 subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True)
                 return True

            # Windows kill
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'LISTENING' in line:
                        parts = line.split()
                        pid = parts[-1]
                        print(f"⚠️  Found existing server on port {port} (PID: {pid})")
                        print(f"🔪 Killing process {pid}...")
                        subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                        time.sleep(2)
                        return True
        except Exception as e:
            print(f"⚠️  Could not kill existing server: {e}")
        return False
    
    def start_frontend_server(self):
        """Start the npm dev server in the background"""
        print("🚀 Starting frontend server...")
        
        # Kill any existing server
        if self._is_port_in_use(5173):
            print("⚠️  Port 5173 is already in use")
            self._kill_existing_server(5173)
            time.sleep(2)
        
        try:
            # Find npm
            npm_path = self._find_npm()
            if not npm_path:
                print("❌ Could not find npm executable!")
                print("   Trying direct npx vite command...")
                npm_path = "npm"  # Fallback to PATH
            else:
                print(f"📍 Found npm at: {npm_path}")
            
            # Helper to run cross-platform
            shell_cmd = True
            if os.name == 'nt':
                 # Windows
                 vite_script = os.path.join(os.getcwd(), "frontend", "node_modules", "vite", "bin", "vite.js")
                 if os.path.exists(vite_script):
                     cmd = f'node "{vite_script}" --port 5173'
                 else:
                     cmd = "cd frontend && npm run dev"
            else:
                 # Mac/Linux
                 cmd = "cd frontend && npm run dev"
            
            print(f"📍 Starting Vite server with command: {cmd}")
            
            self.server_process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=os.getcwd(),
                # Process group for cleaner kill on Unix
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to start...")
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if self._is_port_in_use(5173):
                    print("✅ Server is ready!")
                    time.sleep(2)  # Extra stability wait
                    return True
                
                time.sleep(1)
                elapsed = int(time.time() - start_time)
                if elapsed % 5 == 0 and elapsed > 0:
                    print(f"   Still waiting... ({elapsed}s)")
            
            print("❌ Server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_frontend_server(self):
        """Stop the npm dev server"""
        if self.server_process:
            print("🛑 Stopping frontend server...")
            try:
                # Unix
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.server_process.pid), 15) # SIGTERM
                else:
                    self.server_process.terminate()
                
                self.server_process.wait(timeout=5)
            except Exception as e:
                print(f"Error stopping process: {e}")
                # Force kill
                try:
                    if os.name != 'nt':
                         os.killpg(os.getpgid(self.server_process.pid), 9) # SIGKILL
                    else:
                         self.server_process.kill()
                except:
                    pass
            print("✅ Server stopped")
        
    
    def generate_pdf(self, headless=True):
        """
        Generate PDF using Playwright browser automation
        
        Args:
            headless: Run browser in headless mode (default: True)
            
        Returns:
            str: Path to generated PDF file, or None if failed
        """
        print("\n" + "="*60)
        print("📄 Starting PDF Generation Process")
        print("="*60)
        
        with sync_playwright() as p:
            try:
                # Launch browser
                print(f"🌐 Launching Chromium browser (headless={headless})...")
                browser = p.chromium.launch(headless=headless)
                
                # Create context with download path
                context = browser.new_context(
                    accept_downloads=True,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # Navigate to the website
                print(f"🔗 Navigating to {self.url}...")
                page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for the loading to complete
                print("⏳ Waiting for data to load...")
                try:
                    # Wait for loading spinner to disappear (max 60 seconds)
                    # Adjust selector based on actual loading indicator in frontend
                    # Using a generic approach: waiting for a known element to exist or loading to vanish
                    time.sleep(5) # Initial wait
                    
                    # Try to wait for the date element which usually appears after load
                    # page.wait_for_selector('.date-display', timeout=60000) 
                    print("✅ Assuming data loaded successfully after wait")
                except PlaywrightTimeout:
                    print("⚠️  Loading timeout - proceeding anyway")
                
                # Additional wait for rendering
                time.sleep(3)
                
                # Click the "Save as PDF" button
                print("🖱️  Clicking 'Save as PDF' button...")
                try:
                    # Find and click the Save as PDF button
                    # Look for button that contains "Save" or "PDF"
                    pdf_button = page.locator('button:has-text("Save"), button:has-text("PDF")')
                    if pdf_button.count() > 0:
                         pdf_button = pdf_button.first
                         pdf_button.wait_for(state='visible', timeout=10000)
                         
                         # Set up download listener before clicking
                         with page.expect_download(timeout=120000) as download_info:
                             pdf_button.click()
                             print("⏳ Waiting for PDF generation...")
                         
                         download = download_info.value
                         
                         # Save the downloaded file
                         timestamp = time.strftime("%Y%m%d_%H%M%S")
                         pdf_filename = f"stonkzz-report_{timestamp}.pdf"
                         self.pdf_path = os.path.join(self.download_dir, pdf_filename)
                         
                         download.save_as(self.pdf_path)
                         print(f"✅ PDF saved to: {self.pdf_path}")
                    else:
                        print("❌ Could not find 'Save as PDF' button")
                        return None
                    
                except PlaywrightTimeout:
                    print("❌ Timeout waiting for PDF download")
                    return None
                except Exception as e:
                    print(f"❌ Error during PDF generation: {e}")
                    return None
                
                finally:
                    # Cleanup
                    print("🧹 Cleaning up browser...")
                    browser.close()
                
                return self.pdf_path
                
            except Exception as e:
                print(f"❌ Error in PDF generation: {e}")
                import traceback
                traceback.print_exc()
                import subprocess
                subprocess.run(['playwright', 'install', 'chromium'])
                return None
    
    def generate_and_cleanup(self, headless=True, keep_server_running=False):
        """
        Full workflow: start server, generate PDF, cleanup
        
        Args:
            headless: Run browser in headless mode
            keep_server_running: Keep the server running after PDF generation
            
        Returns:
            str: Path to generated PDF, or None if failed
        """
        try:
            # Start server
            if not self.start_frontend_server():
                return None
            
            # Generate PDF
            pdf_path = self.generate_pdf(headless=headless)
            
            return pdf_path
            
        finally:
            # Cleanup (unless we want to keep server running)
            if not keep_server_running:
                self.stop_frontend_server()


def main():
    """Main entry point for standalone execution"""
    import argparse
    from datetime import datetime
    import pytz
    
    # Log execution time for monitoring
    ist = pytz.timezone('Asia/Kolkata')
    utc = pytz.timezone('UTC')
    
    now_utc = datetime.now(utc)
    now_ist = datetime.now(ist)
    
    print("\n" + "="*60)
    print("📅 EXECUTION TIMESTAMP")
    print("="*60)
    print(f"UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"IST Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Target Schedule: 7:00 AM IST (Weekdays)")
    print("="*60 + "\n")
    
    parser = argparse.ArgumentParser(description='Automated PDF Report Generator')
    parser.add_argument('--skip-server', action='store_true', 
                       help='Skip starting the server (use when server is already running)')
    parser.add_argument('--keep-server', action='store_true',
                       help='Keep the server running after PDF generation')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("StonkzzReport - Automated PDF Generator")
    print("="*60 + "\n")
    
    # Create generator
    generator = PDFReportGenerator()
    
    if args.skip_server:
        # Server is already running, just generate PDF
        print("📡 Using existing server (--skip-server mode)")
        
        # Verify server is running
        if not generator._is_port_in_use(5173):
            print("❌ Server not running on port 5173!")
            print("   Please start the server first or run without --skip-server")
            return 1
        
        print("✅ Server is running on port 5173")
        pdf_path = generator.generate_pdf(headless=True)
    else:
        # Full workflow: start server, generate PDF, cleanup
        pdf_path = generator.generate_and_cleanup(
            headless=True,
            keep_server_running=args.keep_server
        )
    
    if pdf_path and os.path.exists(pdf_path):
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print(f"📄 PDF Report: {pdf_path}")
        print(f"📊 File Size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        print("="*60 + "\n")
        
        # Now send email with attachment
        try:
            # Import dynamically to ensure sys.path is set
            from scripts.email_notifier import send_email_with_attachment
            print("📧 Sending email with PDF attachment...")
            
            success = send_email_with_attachment(
                subject="StonkzzReport - Daily Market Report 📊",
                body=None,  # Use default body
                pdf_path=pdf_path
            )
            
            if success:
                print("✅ Email sent successfully with PDF attachment!")
            else:
                print("⚠️  Email sending failed (check configuration)")
                
        except Exception as e:
            print(f"⚠️  Error sending email: {e}")
            print(f"Details: {e}")
            print("   PDF was generated successfully but email failed")
            # Try absolute import as fallback
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
                from scripts.email_notifier import send_email_with_attachment
                print("   Retrying email with adjusted path...")
                success = send_email_with_attachment(
                    subject="StonkzzReport - Daily Market Report 📊",
                    body=None,  # Use default body
                    pdf_path=pdf_path
                )
                if success: print("✅ Retry success!")
            except Exception as e2:
                print(f"   Retry failed: {e2}")
        
        return 0
    else:
        print("\n" + "="*60)
        print("❌ FAILED to generate PDF")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
