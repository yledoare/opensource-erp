/** @odoo-module */

import { registry } from "@web/core/registry";
import { kanbanView } from '@web/views/kanban/kanban_view';
import { KanbanController } from "@web/views/kanban/kanban_controller";
export class ShopifyKanbanImportController extends KanbanController {
    setup() {
        super.setup();
    }

    /*
        open the wizard for importing products
    */
    async onClickShopifyProductImport() {
        return this.actionService.doAction("mt_odoo_shopify_connector.action_wizard_shopify_import_product_instance", {});
    }

    /*
        open the wizard for importing customers
    */
    async onClickShopifyCustomerImport() {
        return this.actionService.doAction("mt_odoo_shopify_connector.action_wizard_import_customer", {});
    }

}


export const ShopifyImportKanbanView = {
    ...kanbanView,
    Controller: ShopifyKanbanImportController,
    buttonTemplate: 'ShopifyImportKanban.Buttons',
};

registry.category("views").add('shopify_import_product_k_button', ShopifyImportKanbanView);
registry.category("views").add('shopify_import_customer_k_button', ShopifyImportKanbanView);
