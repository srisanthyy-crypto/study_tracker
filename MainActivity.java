// ============================================================
// MainActivity.java — StudyTrack AI Android App
// Loads the Flask web app inside a WebView
// Place in: app/src/main/java/com/studytrack/app/
// ============================================================

package com.studytrack.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.TextView;

public class MainActivity extends Activity {

    // ── Change this IP to your computer's local IP address ──
    // Run `ipconfig` (Windows) or `ip a` (Linux/Termux) to find it.
    // Example: "http://192.168.1.10:5000"
    // For Termux running on the SAME phone: use "http://localhost:5000"
    private static final String WEB_APP_URL = "http://192.168.1.10:5000";

    private WebView    webView;
    private ProgressBar progressBar;
    private TextView   errorText;
    private long       backPressedTime = 0;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView     = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);
        errorText   = findViewById(R.id.errorText);

        setupWebView();
        webView.loadUrl(WEB_APP_URL);
    }

    /**
     * Configure WebView settings for a full web-app experience.
     */
    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings settings = webView.getSettings();

        // Enable JavaScript (REQUIRED for Flask app)
        settings.setJavaScriptEnabled(true);

        // Enable DOM storage (for localStorage, theme toggle)
        settings.setDomStorageEnabled(true);

        // Allow zoom
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);

        // Responsive layout
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);

        // Cache for offline fallback
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        // Allow mixed content (HTTP inside HTTPS)
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);

        // WebViewClient: keep navigation inside WebView
        webView.setWebViewClient(new WebViewClient() {

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                // Open external links in browser, keep internal links in WebView
                if (url.startsWith("http://192.168") || url.startsWith("http://localhost")
                        || url.startsWith("http://127.0.0.1")) {
                    return false;  // Load inside WebView
                }
                // External URL: open in browser
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                progressBar.setVisibility(View.GONE);
                errorText.setVisibility(View.GONE);
            }

            @Override
            public void onReceivedError(WebView view, int errorCode,
                                        String description, String failingUrl) {
                progressBar.setVisibility(View.GONE);
                // Show helpful error message
                errorText.setVisibility(View.VISIBLE);
                errorText.setText(
                    "⚠️ Cannot connect to Study Tracker!\n\n" +
                    "Make sure:\n" +
                    "1. Flask app is running on your PC/Termux\n" +
                    "2. Both devices are on the same Wi-Fi\n" +
                    "3. IP address in MainActivity.java is correct\n\n" +
                    "Current URL: " + WEB_APP_URL
                );
            }
        });

        // WebChromeClient: handle progress bar
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                if (newProgress < 100) {
                    progressBar.setVisibility(View.VISIBLE);
                    progressBar.setProgress(newProgress);
                } else {
                    progressBar.setVisibility(View.GONE);
                }
            }

            @Override
            public void onReceivedTitle(WebView view, String title) {
                // Optional: set activity title from page title
                // setTitle(title);
            }
        });
    }

    // ── Back button: go back in WebView history ──────────
    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            // Double-press back to exit
            if (System.currentTimeMillis() - backPressedTime < 2000) {
                super.onBackPressed();
            } else {
                backPressedTime = System.currentTimeMillis();
                android.widget.Toast.makeText(this,
                    "Press back again to exit", android.widget.Toast.LENGTH_SHORT).show();
            }
        }
    }

    // ── Lifecycle: pause/resume WebView with activity ────
    @Override
    protected void onResume()  { super.onResume();  webView.onResume(); }
    @Override
    protected void onPause()   { super.onPause();   webView.onPause();  }
    @Override
    protected void onDestroy() { super.onDestroy(); webView.destroy();  }
}
