/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

export class ShopifyListImportController extends ListController {
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
        open the wizard for importing sale order
    */
    async onClickShopifySaleOrderImport() {
        return this.actionService.doAction("mt_odoo_shopify_connector.action_wizard_import_sale_order", {});
    }

    /*
        open the wizard for importing customers
    */
    async onClickShopifyCustomerImport() {
        return this.actionService.doAction("mt_odoo_shopify_connector.action_wizard_import_customer", {});
    }
}


export const ShopifyImportListView = {
    ...listView,
    Controller: ShopifyListImportController,
    buttonTemplate: 'ShopifyImportList.Buttons',
};

registry.category("views").add('shopify_import_product_button', ShopifyImportListView);
registry.category("views").add('shopify_import_sale_order_button', ShopifyImportListView);
registry.category("views").add('shopify_import_customer_button', ShopifyImportListView);

