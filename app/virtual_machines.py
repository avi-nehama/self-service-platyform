import requests
from flask import (
    current_app,
    Blueprint,
    request,
    flash,
    redirect,
    url_for,
    render_template,
)

import pulumi 
import pulumi_azure_native as azure_native

bp = Blueprint("virtual_machines", __name__, url_prefix="/vms")

def create_pulumi_program():
    resource_group = azure_native.resources.ResourceGroup("resourceGroup", location="eastus",  resource_group_name="myResourceGroup")


@bp.route("/", methods=["GET"])
def list_vms():
    vms = []
    return render_template("virtual_machines/index.html")

@bp.route("/new", methods=["GET", "POST"])
def create_vm():
    """creates new vm"""
    if request.method == "POST":
        def pulumi_program():
            return create_pulumi_program()

    # try:
    #     # create a new stack, generating our pulumi program on the fly from the POST body
    #     stack = auto.create_stack(
    #         stack_name=str(stack_name),
    #         project_name=current_app.config["PROJECT_NAME"],
    #         program=pulumi_program,
    #     )
    #     stack.set_config("aws:region", auto.ConfigValue("us-west-2"))
    #     # deploy the stack, tailing the logs to stdout
    #     stack.up(on_output=print)
    #     flash(f"Successfully created site '{stack_name}'", category="success")
    # except auto.StackAlreadyExistsError:
    #     flash(
    #         f"Error: Site with name '{stack_name}' already exists, pick a unique name",
    #         category="danger",
    #     )

    return redirect(url_for("virtual_machines.list_vms"))

