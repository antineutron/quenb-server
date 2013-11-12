 % include head.tpl
    <div class="center">
      <h2>Actions</h2>
      <p>
	    When a client matches a rule, an action is performed - usually displaying a page or an image.
      </p>

      <!--<table id='actionTable' class="table table-striped table-bordered table-condensed">-->
      <table id='actionTable'>
	    <thead>
          <tr><th>Title</th><th>Plugin function call</th><th>Description</th></tr>
		</thead>
		<tbody>
        % for action in actions:
        <tr>
          <td>
            <button class='edit'>Edit action #{{action['id']}}</button>
            <button class='delete'>Delete action #{{action['id']}}</button>
            {{action['title']}}
          </td>
          <td>{{action['module']}}.{{action['function']}}({{action['args'] or ''}})</td>
          <td>{{action['description']}}</td>
        </tr>
        % end for
		</tbody>
	    <tfoot>
          <tr><th>Title</th><th>Plugin function call</th><th>Description</th></tr>
		</tfoot>
      </table>

      <script>
	  	$(function(){
         $( ".edit" ).button({
          icons: {
            primary: "ui-icon-pencil"
          },
          text: false
		});
         $( ".delete" ).button({
          icons: {
            primary: "ui-icon-trash"
          },
          text: false
		});
		});
		$(document).ready(function() {
    		var oTable = $('#actionTable').dataTable();
		} );
      </script>


    </div>
% include tail.tpl
