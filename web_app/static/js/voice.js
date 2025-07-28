class VoiceAssistant {
    constructor() {
        this.isActive = false;
        this.initialized = false;
        
        // Only initialize if we're not on the login page
        if (!window.location.pathname.includes('login')) {
            this.setupEventListeners();
            this.checkStatus();
        }
    }

    async checkStatus() {
        // Don't check status if we're on the login page
        if (window.location.pathname.includes('login')) {
            return;
        }
        
        try {
            const response = await fetch('/api/voice/status', {
                credentials: 'same-origin'
            });
            
            // Handle 401 as a normal case (user not logged in)
            if (response.status === 401) {
                this.initialized = false;
                this.updateUI();
                return;
            }
            
            const data = await this.handleResponse(response);
            
            // Update authentication state
            this.initialized = data.authenticated !== false;
            
            if (this.initialized) {
                this.isActive = data.status === 'running';
                this.updateUI();
            }
        } catch (error) {
            console.error('Error checking voice status:', error);
            // Don't show login prompt for 401 errors as they're handled above
            if (!error.message.includes('401') && !error.message.includes('UNAUTHORIZED')) {
                this.showLoginPrompt();
            }
        }
    }
    
    updateUI() {
        const button = document.getElementById('voiceToggle');
        const status = document.getElementById('voiceStatus');
        
        if (!button || !status) {
            return;
        }
        
        // Don't update UI if we're on the login page
        if (window.location.pathname.includes('login')) {
            return;
        }
        
        if (!this.initialized) {
            button.classList.add('disabled');
            button.title = 'Please log in to use voice assistant';
            if (status) {
                status.textContent = 'Login Required';
                status.classList.remove('active');
            }
            return;
        }
        
        button.classList.remove('disabled');
        button.title = '';
        
        if (this.isActive) {
            button.classList.add('active');
            status.classList.add('active');
            status.textContent = 'Voice Active';
        } else {
            button.classList.remove('active');
            status.classList.remove('active');
            status.textContent = 'Voice Inactive';
        }
    }

    async toggleVoice() {
        const button = document.getElementById('voiceToggle');
        const status = document.getElementById('voiceStatus');
        
        try {
            if (!this.initialized) {
                this.showLoginPrompt();
                return;
            }
            
            if (this.isActive) {
                await this.stopVoice();
                this.isActive = false;
            } else {
                await this.startVoice();
                this.isActive = true;
            }
            this.updateUI();
        } catch (error) {
            console.error('Error toggling voice:', error);
            alert('Error: ' + error.message);
        }
    }

    async startVoice() {
        try {
            const csrfToken = this.getCSRFToken();
            const response = await fetch('/api/voice/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'  // Important for cookies/session
            });
            
            const data = await this.handleResponse(response);
            return data;
        } catch (error) {
            console.error('Error in startVoice:', error);
            throw new Error('Failed to start voice assistant: ' + error.message);
        }
    }

    async stopVoice() {
        try {
            const csrfToken = this.getCSRFToken();
            const response = await fetch('/api/voice/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'  // Important for cookies/session
            });
            
            const data = await this.handleResponse(response);
            return data;
        } catch (error) {
            console.error('Error in stopVoice:', error);
            throw new Error('Failed to stop voice assistant: ' + error.message);
        }
    }
    
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (!metaTag) {
            console.warn('CSRF token meta tag not found');
            return '';
        }
        return metaTag.getAttribute('content') || '';
    }
    
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        // Handle unauthorized (401) responses
        if (response.status === 401) {
            this.initialized = false;
            this.updateUI();
            throw new Error('Authentication required. Please log in to use this feature.');
        }
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            // Update authentication state based on response
            if (typeof data.authenticated !== 'undefined') {
                this.initialized = data.authenticated;
            }
            
            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }
            
            return data;
        } else {
            const text = await response.text();
            console.error('Unexpected response:', text);
            
            // Check for login page in response
            if (text.includes('login') || text.includes('sign in')) {
                this.initialized = false;
                this.updateUI();
                throw new Error('Please log in to continue');
            }
            
            throw new Error('Received unexpected response from server');
        }
    }

    showLoginPrompt() {
        // Don't show login prompt if we're already on the login page
        if (window.location.pathname.includes('login')) {
            return;
        }
        
        // Only show one prompt at a time
        if (this.showingLoginPrompt) return;
        this.showingLoginPrompt = true;
        
        // Show a login modal or redirect to login page
        const loginUrl = '/login?next=' + encodeURIComponent(window.location.pathname);
        
        // Use a more subtle notification instead of alert
        const notification = document.createElement('div');
        notification.className = 'voice-login-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <p>Please log in to use the voice assistant</p>
                <div class="notification-buttons">
                    <button class="btn-notification" id="voiceLoginBtn">Log In</button>
                    <button class="btn-notification btn-cancel">Not Now</button>
                </div>
            </div>
        `;
        
        // Add styles if not already added
        if (!document.getElementById('voice-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'voice-notification-styles';
            style.textContent = `
                .voice-login-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    z-index: 1000;
                    max-width: 300px;
                }
                .notification-buttons {
                    display: flex;
                    gap: 10px;
                    margin-top: 10px;
                }
                .btn-notification {
                    padding: 5px 10px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                #voiceLoginBtn {
                    background: #4CAF50;
                    color: white;
                }
                .btn-cancel {
                    background: #f0f0f0;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Add to document
        document.body.appendChild(notification);
        
        // Add event listeners
        document.getElementById('voiceLoginBtn').addEventListener('click', () => {
            window.location.href = loginUrl;
        });
        
        notification.querySelector('.btn-cancel').addEventListener('click', () => {
            notification.remove();
            this.showingLoginPrompt = false;
        });
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.remove();
                this.showingLoginPrompt = false;
            }
        }, 10000);
    }

    setupEventListeners() {
        const button = document.getElementById('voiceToggle');
        if (button) {
            button.addEventListener('click', (e) => {
                if (!this.initialized) {
                    e.preventDefault();
                    this.showLoginPrompt();
                    return;
                }
                this.toggleVoice();
            });
            
            // Add tooltip for better UX
            button.setAttribute('data-tooltip', 'Log in to use voice assistant');
        }
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.voiceAssistant = new VoiceAssistant();
});