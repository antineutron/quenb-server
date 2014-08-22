all: static/js/quenb-all.js static/js/quenb-all.min.js 

static/js/quenb-all.js: static/js/zepto.min.js static/js/quenb.js
	cat static/js/zepto.min.js static/js/quenb.js > static/js/quenb-all.js

static/js/quenb-all.min.js: static/js/zepto.min.js static/js/quenb.min.js
	cat static/js/zepto.min.js static/js/quenb.min.js > static/js/quenb-all.min.js

static/js/quenb.min.js: static/js/quenb.js
	slimit -m static/js/quenb.js > static/js/quenb.min.js

