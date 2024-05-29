/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { getColor } from "@web/core/colors/colors";
import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

export class ShopifyDashboardGraph extends Component {

    static template = "mt_odoo_shopify_connector.shopify_graph_dashboard_widget";
    static props = {
        ...standardFieldProps,
        graphType: String,
    };

    setup() {
        super.setup()
        this.chart = null;
        this.canvasRef = useRef("canvas");
        this.data = "";
        if (this.props.record.data[this.props.name]) {
            this.data = JSON.parse(this.props.record.data[this.props.name]);
        }
        this.actionService = useService("action");
        this.orm = useService("orm");

        onWillStart(async () => await loadBundle("web.chartjs_lib"));

        useEffect(() => {
            
            if (this.data) {
                this.renderGraphChart();
            }

            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }

    // Render graph(Chart.js) with config

    renderGraphChart() {

        if (this.chart) {
            this.chart.destroy();
        }
        let config;
        if (this.props.graphType === "line") {
            config = this.getLineChartConfig();
        } else if (this.props.graphType === "bar") {
            config = this.getBarChartConfig();
        }
        this.chart = new Chart(this.canvasRef.el, config);
    }

    getLineChartConfig() {
        const data = [];
        const labels = this.data.values.map(function (pt) {
            return pt.x;
        });

        if (this.data && this.data.values) {
            this.data.values.forEach(function (pt) {
                data.push(pt.y);
            });
        }

        return {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        backgroundColor:'#7735bc80',
                        borderColor:'#7735bc',
                        data,
                        label: this.data.key,
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                legend: { display: false },
                scales: {
                    xAxes: [{
                        position: 'bottom'
                    }],
                    yAxes: [{
                        position: 'left',
                        ticks: {
                            beginAtZero: true
                        },
                    }]
                },
                maintainAspectRatio: false,
                elements: {
                    line: {
                        tension: 0.0002,
                    },
                },
                tooltips: {
                    intersect: false,
                    position: "nearest",
                    caretSize: 0,
                },
            },
        };
    }

    getBarChartConfig() {
        const data = [];
        const labels = [];
        const backgroundColor = [];

        if (this.data && this.data.values) {
            this.data.values.forEach(function (pt) {
                data.push(pt.y);
                labels.push(pt.x);

                const color =
                    pt.type === "past" ? getColor(13) : pt.type === "future" ? getColor(19) : "#ebebeb";
                backgroundColor.push(color);
            });
        }

        return {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        backgroundColor:'#7735bc',
                        data,
                        fill: "start",
                        label: this.data.key,
                        borderWidth: 2,
                        pointStyle: 'bar',
                    },
                ],
            },
            options: {
                legend: {display: false},
                scales: {
                    x: [{
                        position: 'bottom'
                    }],
                    y: [{
                        position: 'left',
                        ticks: {
                            beginAtZero: true
                        },
                    }]
                },
                maintainAspectRatio: false,
                elements: {
                    line: {
                        tension: 0.5,
                    }
                },
                tooltips: {
                    intersect: false,
                    position: 'nearest',
                    caretSize: 0,
                },
            },
        };
    }

    async _sortOrders(e) {
        const currentDashboard = e.currentTarget

        const [record] = await this.orm.read(this.props.record.resModel, [this.props.record.resId], ["dashboard_graph_data"], { context: {'sort':  e.currentTarget.value} });
        this.data = JSON.parse(record.dashboard_graph_data);
        // console.log("Data in sort")
        // console.log(this.data)
        currentDashboard.closest(".dashboard_graph_shopify").querySelector("#instance_order .order_count").innerHTML = this.data.shop_orders.order_count
        currentDashboard.closest(".dashboard_graph_shopify").querySelector(".total_sale").innerHTML = this.data.shop_currency_symbol + this.data.sales_total
        this.renderGraphChart();
    }

    _GraphBarCharts(e) {
        this._GraphCharts("bar", e)
    }

    _GraphLineCharts(e) {
        this._GraphCharts("line", e)
    }  

    async _GraphCharts(graphType, e) {
        const graph_period = e.currentTarget.closest(".graph_top_menu").querySelector(".select_time_period #sort_order_data").value
        const [record] = await this.orm.read(this.props.record.resModel, [this.props.record.resId], ["dashboard_graph_data"], { context: {'sort':  graph_period} });
        this.props.graphType = graphType
        this.data = JSON.parse(record.dashboard_graph_data);
        this.renderGraphChart();
    }  

    _SyncedProducts() {
        return this.actionService.doAction(this.data.shop_products.product_action, {})
    }

    _SyncedCustomers() {
        return this.actionService.doAction(this.data.shop_customers.customer_action, {})
    }

    _SyncedOrders() {
        return this.actionService.doAction(this.data.shop_orders.order_action, {})
    }

}

export const ShopifyDashboardGraphs = {
    component: ShopifyDashboardGraph,
    supportedTypes: ["text"],
    extractProps: ({ attrs }) => ({
        graphType: attrs.graph_type,
    }),
}

registry.category("fields").add("shopify_dashboard_graph", ShopifyDashboardGraphs);