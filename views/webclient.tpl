<html>
<head>
<style type="text/css">

body {
    margin: 0;
}
iframe#contentpane {
    border: 0;
    width: 100%;
    height: 100%;
}

/* from http://css-tricks.com/perfect-full-page-background-image/ */
img.bg {
  /* Set rules to fill background */
  min-height: 100%;
  min-width: 1024px;

  /* Set up proportionate scaling */
  width: 100%;
  height: auto;

  /* Set up positioning */
  position: fixed;
  top: 0;
  left: 0;
}

@media screen and (max-width: 1024px) {
/* Specific to this particular image */
  img.bg {
    left: 50%;
    margin-left: -512px;   /* 50% */
  }
}

.hidden {
    display: none;
}

</style>
<!-- Download jquery from their CDN -->
<script src="/static/js/jquery-1.9.1.min.js"></script>
<script src="/static/js/jquery-migrate-1.1.1.min.js"></script>

<!-- Include notification stuff (noty) -->
<script src="/static/js/noty/jquery.noty.js"></script>
<script src="/static/js/noty/layouts/all.js"></script>
<script src="/static/js/noty/themes/default.js"></script>

<script>
var server_supplied_cid = "{{client_id}}";
var our_ip = "{{addr}}";

var client_query = {
    %for key,value in query_variables.items():
    {{key}}: "{{value}}",
    %end
};
</script>

<!-- The main stuff is here. -->
<script src=/static/js/quenb.js></script>

</head>
<body>
    <!-- Special item e.g. to display when things go wrong -->
    <img id="tvstatic" class="bg hidden special" src="/static/images/tvstatic.gif">

	<!-- As above, but we can use this to display an arbitrary image fullscreen -->
    <img id="imgfullscreen" class="bg hidden" src="/static/images/tvstatic.gif">

	<iframe id="contentpane"></iframe>
</body>
</html>
