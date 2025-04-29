export default class TrustindexCommon {
	static setCommonConstants()
	{
		this.script = document.currentScript;
		this.loadedCss = [];
		this.loadedJs = [];
	}

	static addCSS(url, callback, checkIframe = false, error = null)
	{
		if (typeof this.loadedCss === 'undefined') {
			this.loadedCss = [];
		}

		if (!url || this.loadedCss.indexOf(url) !== -1) {
			return callback ? callback() : null;
		}

		let link = document.createElement('link');

		link.type = 'text/css';
		link.rel = 'stylesheet';
		link.href = url;

		if (checkIframe && window !== window.parent && this.isCrossDomainIframe()) {
			window.parent.document.head.appendChild(link);
		} else {
			document.head.appendChild(link);
		}

		document.head.appendChild(link);

		if ('function' === typeof callback) {
			link.addEventListener('load', callback);
		}

		if ('function' === typeof error) {
			link.addEventListener('error', error);
		}

		return this.loadedCss.push(url);
	}

	static addJS(url, callback, checkIframe = false)
	{
		if (typeof this.loadedJs === 'undefined') {
			this.loadedJs = [];
		}

		if (!url || this.loadedJs.indexOf(url) !== -1) {
			return callback ? callback() : null;
		}

		let script = document.createElement('script');

		script.type = 'text/javascript';
		script.src = url;

		if (checkIframe && window !== window.parent && this.isCrossDomainIframe()) {
			window.parent.document.head.appendChild(script);
		} else {
			document.head.appendChild(script);
		}

		if (callback) {
			script.addEventListener('load', callback);
		}

		return this.loadedJs.push(url);
	}

	static openWindow(url)
	{
		let a = document.createElement('a');

		a.href = url;
		a.target = '_blank';
		a.rel = 'noopener noreferrer nofollow';

		return a.click();
	}

	static getScriptSelector(id)
	{
		return '[src*=".trustindex."][src*="'+ id +'.js"],[data-src*=".trustindex."][data-src*="'+ id +'.js"]';
	}

	static getScriptKey(script)
	{
		let src = (script.getAttribute('data-src') || script.getAttribute('src'));
		let key = src.replace(/.+\?([^&]+)/, '$1');
		if (!key || key === src || key.indexOf('=') !== -1) {
			return null;
		}

		return key;
	}

	static getCDNUrl()
	{
		if (typeof this.cdnUrl !== 'undefined' && this.cdnUrl) {
			return this.cdnUrl;
		}

		let url = 'https://cdn.trustindex.io/';

		if (this.script && this.script.src) {
			let parts = this.script.src.split('/');

			parts.pop(); // flush *.js from the end

			url = parts.join('/') + '/';
		}

		// url does not seem to come from any trustindex link
		if (-1 === url.indexOf('trustindex.')) {
			url = 'https://cdn.trustindex.io/';
		}

		this.cdnUrl = url;

		return url;
	}

	static getWidgetUrl(pid)
	{
		if (typeof pid === 'undefined') {
			return null;
		}

		return this.getCDNUrl() + 'widgets/' + pid.substring(0, 2) + '/' + pid + '/';
	}

	static getDecodedHtml(html)
	{
		let txt = document.createElement('textarea');
		txt.innerHTML = html;

		return txt.value;
	}

	static getRelativeTime(timestamp, locale)
	{
		let intervals = locale.split('|'); // %d %s ago|today|day|days|week|weeks|month|months|year|years
		let format = intervals.shift(); // %d %s ago
		let todayStr = intervals.shift(); // "today"

		let periods = [
			86400, // day ago
			604800, // week ago
			2419200, // month ago
			31536000 // year ago
		];

		let seconds = (new Date().getTime() / 1000) - timestamp;
		for (let i = periods.length - 1; i >= 0; i--) {
			if (seconds >= periods[i]) {
				let amount = Math.floor(seconds / periods[i]);
				let intervalIndex = i * 2;

				if (amount > 1) {
					intervalIndex++;
				}

				return format.replace('%d', amount).replace('%s', intervals[intervalIndex]);
			}
		}

		return todayStr;
	}

	static getDevicePixelRatio()
	{
		let ratio = 1;

		if (window.screen.systemXDPI !== undefined && window.screen.logicalXDPI !== undefined && window.screen.systemXDPI > window.screen.logicalXDPI) {
			ratio = window.screen.systemXDPI / window.screen.logicalXDPI;
		} else if (window.devicePixelRatio !== undefined) {
			ratio = window.devicePixelRatio;
		}

		return Math.min(ratio, 2);
	}

	static getDefaultAvatarUrl()
	{
		let r = (Math.floor(Math.random() * 10) + 1);

		return this.getCDNUrl() + 'assets/default-avatar/noprofile-' + (r < 10 ? '0' : '') + r + '.svg';
	}

	static getPageLanguage()
	{
		return (document.documentElement.lang || 'en').substr(0, 2).toLowerCase();
	}

	static getUserLanguage()
	{
		return (navigator.language || navigator.userLanguage || this.getPageLanguage()).substr(0, 2).toLowerCase();
	}

	static isAdminUrl(url)
	{
		let currentLocation = url ? new URL(url) : location;

		return /(admin|test)\.trustindex/.test(currentLocation.hostname) && -1 === currentLocation.href.indexOf('test/widget.html');
	}

	static isAdminEditUrl(url)
	{
		if (typeof url === 'undefined') {
			url = location.href;
		}

		return -1 !== url.indexOf('widget/edit');
	}

	static isCrossDomainIframe()
	{
		// not an iframe
		if (window.parent === window) {
			return false;
		}

		try {
			let parentLocation = new URL(window.parent.location);

			return (parentLocation.protocol !== location.protocol || parentLocation.hostname !== location.hostname || parentLocation.port !== location.port);
		} catch (error) {
			console.error(error);

			return null;
		}
	}

	static isMobileDevice()
	{
		if (this.isAdminUrl() && !this.isAdminEditUrl()) {
			return !!document.querySelector('.widget-editor.mobile');
		}

		return /mobi/i.test(navigator.userAgent || navigator.vendor || window.opera);
	}

	static isWebpSupported(callback)
	{
		if (typeof this.cacheWebpSupported !== 'undefined') {
			return callback(this.cacheWebpSupported);
		}

		let done = (result) => {
			this.cacheWebpSupported = result;
			return callback(result);
		};

		let img = new Image();
		img.onload = () => done(img.width > 0 && img.height > 0);
		img.onerror = () => done(false);
		img.src = 'data:image/webp;base64,UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA';
	}

	static isDarkMode()
	{
		return window?.matchMedia?.('(prefers-color-scheme:dark)')?.matches ? true : false;
	}

	static waitForVisibility(content, callback, timeout = 0)
	{
		if (content.offsetWidth > 0) {
			if (timeout) {
				return setTimeout(callback, timeout);
			}

			return callback();
		}

		new ResizeObserver(function(entries) {
			if (entries[0].target.offsetWidth > 0) {
				callback();
				this.disconnect();
			}
		}).observe(content);
	}
};