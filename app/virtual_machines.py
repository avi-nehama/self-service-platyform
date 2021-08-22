from flask import (
    current_app,
    Blueprint,
    request,
    flash,
    redirect,
    url_for,
    render_template,
)

import pulumi_azure_native as azure_native
import pulumi.automation as auto
import pulumi


bp = Blueprint("virtual_machines", __name__, url_prefix="/vms")

LOCATION = "eastus"

def create_pulumi_program(env_name: str):
    resource_group = azure_native.resources.ResourceGroup("resourceGroup", location=LOCATION,  resource_group_name=env_name)

    virtual_network = azure_native.network.VirtualNetwork("virtualNetwork",
        address_space=azure_native.network.AddressSpaceArgs(
            address_prefixes=["10.0.0.0/16"],
        ),
        location="eastus",
        resource_group_name=resource_group.name,
        virtual_network_name="vnet1"
    )

@bp.route("/", methods=["GET"])
def list_vms():
    vms = []
    org_name = current_app.config["PULUMI_ORG"]
   
    project_name = current_app.config["PROJECT_NAME"]
    try:
        ws = auto.LocalWorkspace(
            project_settings=auto.ProjectSettings(name=project_name, runtime="python")
        )
        all_stacks = ws.list_stacks()
        for stack in all_stacks:
            stack = auto.select_stack(
                stack_name=stack.name,
                project_name=project_name,
                # no-op program, just to get outputs
                program=lambda: None,
            )
            outs = stack.outputs()
            vms.append(
                {
                    "name": stack.name,
                }
            )

    except Exception as exn:
        flash(f"{str(exn)}", category="danger") 


    return render_template("virtual_machines/index.html", vms=vms)

@bp.route("/new", methods=["GET", "POST"])
def create_vm():
    """creates new vm"""
    if request.method == "POST":
        stack_name = request.form.get("site-id")

        def pulumi_program():
            return create_pulumi_program(str(stack_name)) 
    
        try:
            # create a new stack, generating our pulumi program on the fly from the POST body
            stack = auto.create_stack(
                stack_name=str(stack_name),
                project_name=current_app.config["PROJECT_NAME"],
                program=pulumi_program,
            )
            stack.set_config("aws:region", auto.ConfigValue("us-west-2"))
            # deploy the stack, tailing the logs to stdout
            stack.up(on_output=print)
            flash(f"Successfully created environment '{stack_name}'", category="success")
        except auto.StackAlreadyExistsError:
            flash(
                f"Error: Environment with name '{stack_name}' already exists, pick a unique name",
                category="danger",
            )
        except auto.CommandError as e:
            flash(
                f"Error: {format(e)}",
                category="danger",
            )


        return redirect(url_for("virtual_machines.list_vms"))
    return render_template("virtual_machines/create.html")

@bp.route("/<string:id>/delete", methods=["POST"])
def delete_vm(id: str):
    stack_name = id
    try:
        stack = auto.select_stack(
            stack_name=stack_name,
            project_name=current_app.config["PROJECT_NAME"],
            # noop program for destroy
            program=lambda: None,
        )
        stack.destroy(on_output=print)
        stack.workspace.remove_stack(stack_name)
        flash(f"Site '{stack_name}' successfully deleted!", category="success")
    except auto.ConcurrentUpdateError:
        flash(
            f"Error: Site '{stack_name}' already has update in progress",
            category="danger",
        )
    except Exception as exn:
        flash(str(exn), category="danger")

    return redirect(url_for("virtual_machines.list_vms"))
