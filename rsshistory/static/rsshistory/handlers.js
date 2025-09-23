
class YouTubeVideoHandler {
    constructor(url) {
        this.originalUrl = url;
        this.videoId = this.extractVideoId(url);
    }

    extractVideoId(url) {
        try {
            const urlObj = new URL(url);
            const hostname = urlObj.hostname;

            if (hostname.includes("youtu.be")) {
                return urlObj.pathname.slice(1);
            }

            if (urlObj.searchParams.has("v")) {
                return urlObj.searchParams.get("v");
            }

            const paths = urlObj.pathname.split("/");
            const validPrefixes = ["embed", "shorts", "v"];
            if (validPrefixes.includes(paths[1]) && paths[2]) {
                return paths[2];
            }

            return null;
        } catch (e) {
            return null;
        }
    }

    getUrl() {
        if (!this.videoId) return null;
        return `https://www.youtube.com/watch?v=${this.videoId}`;
    }

    isHandledBy() {
        return !!this.videoId;
    }

    getFeeds() {
       return [];
    }

    getPreviewHtml() {
        if (!this.videoId) return null;
    
        const embedUrl = `https://www.youtube.com/embed/${this.videoId}`;
        return `
            <div class="youtube_player_container mb-4">
                <iframe 
                    src="${embedUrl}" 
                    frameborder="0" 
                    allowfullscreen 
                    class="youtube_player_frame w-100" 
                    style="aspect-ratio: 16 / 9;"
                    referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            </div>
        `;
    }

    getEmbedUrl() {
        if (!this.videoId) return null;
    
        return `https://www.youtube.com/embed/${this.videoId}`;
    }
}


class YouTubeChannelHandler {
    constructor(url) {
        this.originalUrl = url;
        this.channelId = this.extractChannelId(url);
    }

    extractChannelId(url) {
        try {
            const urlObj = new URL(url);
            const paths = urlObj.pathname.split("/").filter(Boolean);

            if (paths[0] === "channel" && paths[1]) {
                return paths[1];
            }

            return null;
        } catch (e) {
            return null;
        }
    }

    getUrl() {
        if (!this.channelId) return null;
        return `https://www.youtube.com/channel/${this.channelId}`;
    }

    isHandledBy() {
        return !!this.channelId;
    }

    getFeeds() {
        if (!this.channelId) return [];
        return [`https://www.youtube.com/feeds/videos.xml?channel_id=${this.channelId}`];
    }

    getPreviewHtml() {
       return null;
    }
}


class RedditHandler {
    constructor(url) {
        this.originalUrl = url;
        this.subreddit = this.extractSubreddit(url);
    }

    extractSubreddit(url) {
        try {
            const urlObj = new URL(url);
            const paths = urlObj.pathname.split("/").filter(Boolean); // remove empty segments

            // Match /r/subreddit_name
            if (paths[0] === "r" && paths[1]) {
                return paths[1];
            }

            return null;
        } catch (e) {
            return null;
        }
    }

    getUrl() {
        if (!this.subreddit) return null;
        return `https://www.reddit.com/r/${this.subreddit}/`;
    }

    isHandledBy() {
        return !!this.subreddit;
    }

    getFeeds() {
        if (!this.subreddit) return [];
        return [`https://www.reddit.com/r/${this.subreddit}/.rss`];
    }

    getPreviewHtml() {
        return null;
    }
}


function getUrlHandler(link) {
    let handler = new YouTubeVideoHandler(link);
    if (handler.isHandledBy())
    {
        return handler;
    }

    handler = new YouTubeChannelHandler(link);
    if (handler.isHandledBy())
    {
        return handler;
    }

    handler = new RedditHandler(link);
    if (handler.isHandledBy())
    {
        return handler;
    }
}
