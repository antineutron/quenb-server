 % include head.tpl
    <div class="center">
      <h2>Rules</h2>
      <p>
        Rules are used to identify a client and get it to perform an action (such as displaying a page).
        This is the current list of rules in the database:
      </p>

      <table id='ruleTable'>
	    <thead>
          <tr><th>Priority</th><th>Rule</th><th>Action</th></tr>
		</thead>
		<tbody>
        % for rule in rules:
        <tr>
          <td>
            <button class='edit'>Edit rule #{{rule['id']}}</button>
            <button class='delete'>Delete rule #{{rule['id']}}</button>
            {{rule['priority']}}
          </td>
          <td>{{rule['rule']}}</td>
          <td>{{rule['title']}} - Calls: {{rule['module']}}.{{rule['function']}}({{rule['args'] or ''}})</td>
        </tr>
		</tbody>
        % end for
	    <tfoot>
          <tr><th>Priority</th><th>Rule</th><th>Action</th></tr>
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
            var oTable = $('#ruleTable').dataTable();
        } );
      </script>


    </div>
% include tail.tpl