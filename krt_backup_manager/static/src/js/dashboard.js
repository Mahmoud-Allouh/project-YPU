/** @odoo-module */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, onWillUnmount, onMounted, useState, useRef } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { user } from "@web/core/user";

export class MessageZoneComponent extends Component {
    static template = "krt_backup_manager.MessageZone";
    static props = {
        ...standardFieldProps,
        message: { type: String, optional: true },
        icon: { type: Boolean, optional: true },
    };
    static defaultProps = {
        message: "",
        icon: false
    };

    setup() {
        super.setup();
    }
}


export class BackupRestoreDashboardView extends Component {

    setup() {
        super.setup();
        this.resizeTimeout = null;
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.popover = useService("popover");

        useBus(this.env.bus, 'resize', (ev) => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.initializeChart();
            }, 300);
        });

        this.state = useState({
            page: "apercu",
            onPageChange: false,

            backupHistory: [],
            history_chart_type: "bar",
            successStates: [],
            success_chart_type: "doughnut",

            instance_total: 0,
            instance_pourcentage_presence: 0,
            configs_total: 0,
            configs_active: 0,
            pourcentage_instance_success: 0,
            pourcentage_instance_fail: 0,
            fichier_present_file_size: "-",
            fichier_absent_file_size: "-",

            last_dashboard_instance_list: [],
            all_instance_list: [],

            configs_active_list: [],
            all_configs_list: [],

            activeMenu: null,
            limit: 25,
            offset: 0,

            moreDataAreLoading: false
        });

        this.chart_history = null;
        this.chart_history_container = useRef("historyChart");

        this.chart_historyConfig = {
            type: this.state.history_chart_type,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 10
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 40,
                            padding: 10,
                        }
                    }
                },
                layout: {
                    padding: {
                        left: 10,
                        right: 10,
                        top: 10,
                        bottom: 30
                    }
                },
                animation: {
                    duration: 500
                }
            }
        };

        this.chart_success = null;
        this.chart_success_container = useRef("successChart");

        this.chart_successConfig = {
            type: this.state.success_chart_type,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 40,
                            padding: 10,
                        }
                    },
                },
                layout: {
                    padding: {
                        left: 10,
                        right: 10,
                        top: 5,
                        bottom: 35
                    }
                },
                animation: {
                    duration: 500
                }
            }
        };

        onMounted(() => {
            document.addEventListener('click', (event) => {
                if (this.state.activeMenu && !event.target.closest('.menu-button')) {
                    this.state.activeMenu.classList.remove('active');
                    this.state.activeMenu = null;
                }
            });

            // Tab management
            const tabs = document.querySelectorAll('.auto-backup-dashboard-container .tab');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                });
            });

            // Hover effect sur les cartes de statistiques
            const statCards = document.querySelectorAll('.auto-backup-dashboard-container .stat-card');
            statCards.forEach(card => {
                card.addEventListener('mouseover', () => {
                    card.style.transform = 'translateY(-2px)';
                    card.style.transition = 'transform 0.2s ease';
                });
                card.addEventListener('mouseout', () => {
                    card.style.transform = 'translateY(0)';
                });
            });

            this.initializeChart();
        });
        onWillUnmount(() => {
            this.destroyChartHistory();
            this.destroyChartSuccess();
        });
        onWillStart(async () => {
            this.has_restore_group = await user.hasGroup("krt_backup_manager.module_krt_backup_manager_restore_group");
            this.has_download_group = await user.hasGroup("krt_backup_manager.module_krt_backup_manager_download_group");
            this.has_delete_group = await user.hasGroup("krt_backup_manager.module_krt_backup_manager_delete_group");

            await this.loadDatas();
            this.storageInit();
        });
    }

    get lastInstanceCount() {
        return (this.state.last_dashboard_instance_list) ? this.state.last_dashboard_instance_list.length : 0;
    }

    storageInit() {
        const store_page = localStorage.getItem("store:Page") || "apercu";
        this.state.page = store_page;
        localStorage.setItem("store:Page", store_page);

        const historyChartType = localStorage.getItem("store:HistoryChartType") || "bar";
        this.state.history_chart_type = historyChartType;
        localStorage.setItem("store:HistoryChartType", historyChartType);

        const successChartType = localStorage.getItem("store:SuccessChartType") || "doughnut";
        this.state.success_chart_type = successChartType;
        localStorage.setItem("store:SuccessChartType", successChartType);
    }
    initializeChart() {
        try {
            this.initializeHistoryChart();
        } catch (error) {
            console.log(error);
        }
        try {
            this.initializeSuccessChart();
        } catch (error) {
            console.log(error);
        }
    }
    initializeHistoryChart() {
        this.chart_historyConfig.type = this.state.history_chart_type;
        const ctx = this.chart_history_container.el.getContext('2d');
        this.destroyChartHistory();
        this.chart_history = new Chart(ctx, {
            ...this.chart_historyConfig,
            data: {

                labels: this.state.backupHistory.map(item => item[0]),
                datasets: [
                    {
                        label: _t("Total backups"),
                        data: this.state.backupHistory.map(item => (item[1].success + item[1].fail)),
                        borderColor: '#6366f1',
                        backgroundColor: (this.state.history_chart_type == 'line') ? '#6366f120' : '#6366f1',
                        borderWidth: 1,
                        fill: true
                    },
                    {
                        label: _t("Successful backups"),
                        data: this.state.backupHistory.map(item => item[1].success),
                        borderColor: '#4ade80',
                        backgroundColor: (this.state.history_chart_type == 'line') ? '#4ade8020' : '#4ade80',
                        borderWidth: 1,
                        fill: true
                    }
                ]
            }
        });
        return this.chart_history;
    }
    initializeSuccessChart() {
        this.chart_successConfig.type = this.state.success_chart_type;
        const ctx = this.chart_success_container.el.getContext('2d');
        this.destroyChartSuccess();
        this.chart_success = new Chart(ctx, {
            ...this.chart_successConfig,
            data: {
                labels: this.get_this_key_from_object("label", this.state.successStates),
                datasets: [
                    {
                        data: this.get_this_key_from_object("value", this.state.successStates),
                        backgroundColor: ['#4ade80', '#f87171'],
                    },
                ]
            }
        });
        return this.chart_success;
    }
    setHistoryChartType(history_chart_type) {
        // ["line", "bar"]
        this.state.history_chart_type = history_chart_type;
        localStorage.setItem("store:HistoryChartType", history_chart_type);
        this.initializeHistoryChart();
    }
    setSuccessChartType(success_chart_type) {
        // ["pie", "doughnut"]
        this.state.success_chart_type = success_chart_type;
        localStorage.setItem("store:SuccessChartType", success_chart_type);
        this.initializeSuccessChart();
    }
    async loadMoreInstance() {
        this.state.moreDataAreLoading = true;
        let backup_instance_datas = await this.orm.call("db.backup.configure", "dashboard_global_backup_instance_datas", [], {
            "limit": this.state.limit,
            "offset": this.state.offset
        });
        this.state.limit = backup_instance_datas.limit;
        this.state.offset = (this.state.offset + backup_instance_datas.instances.length);
        setTimeout(() => {
            this.state.moreDataAreLoading = false;
            this.state.all_instance_list.push(...backup_instance_datas.instances);
        }, 100);
    }
    async loadDatas() {
        let datas = await this.orm.call("db.backup.configure", "dashboard_global_datas", []);
        await this.loadMoreInstance();

        this.state.instance_total = datas.instance_total;
        this.state.instance_pourcentage_presence = datas.instance_pourcentage_presence;
        this.state.configs_total = datas.configs_total;
        this.state.configs_active = datas.configs_active;
        this.state.pourcentage_instance_success = datas.pourcentage_instance_success;
        this.state.pourcentage_instance_fail = datas.pourcentage_instance_fail;
        this.state.fichier_present_file_size = datas.fichier_present_file_size;
        this.state.fichier_absent_file_size = datas.fichier_absent_file_size;

        this.state.last_dashboard_instance_list = datas.last_dashboard_instance_list;
        this.state.configs_active_list = datas.configs_active_list;
        this.state.all_configs_list = datas.all_configs_list;
        this.state.backupHistory = datas.backupHistory;

        this.state.successStates = [
            {
                label: _t("Successes"),
                value: this.state.pourcentage_instance_success,
            },
            {
                label: _t("Failures"),
                value: this.state.pourcentage_instance_fail,
            }
        ];

        return true;
    }
    goToPage(page) {
        if (!this.state.onPageChange) {
            this.state.onPageChange = true;
            this.state.page = page;
            if (this.state.page == 'apercu') {
                setTimeout(() => {
                    this.initializeChart();
                    this.state.onPageChange = false;
                }, 100);
            } else {
                this.state.onPageChange = false;
            }
        }
        localStorage.setItem("store:Page", page);
    }
    destroyChartHistory() {
        if (this.chart_history) {
            this.chart_history.destroy();
        }
    }
    destroyChartSuccess() {
        if (this.chart_success) {
            this.chart_success.destroy();
        }
    }
    get_this_key_from_object(field, datas) {
        return datas.map(item => item[field]);
    }
    showMessage(ev, message) {
        if (message) {
            this.popover.add(
                ev.currentTarget,
                this.constructor.components.MessageContainer,
                {
                    message: message
                },
                {
                    position: "bottom",
                    closeOnClickAway: true,
                }
            );
        }
    }
    showAlert(ev, message) {
        if (message) {
            this.popover.add(
                ev.currentTarget,
                this.constructor.components.MessageContainer,
                {
                    message: message,
                    icon: true
                },
                {
                    position: "bottom",
                    closeOnClickAway: true,
                }
            );
        }
    }
    async toggleConfigStatus(resId, status) {
        const data = {
            active: (!status)
        };
        await this.orm.write("db.backup.configure", [resId], data);
        await this.loadDatas();
    }
    async refreshDashboardDatas() {
        let promise = await this.loadDatas();
        this.initializeChart();
        return promise;
    }
    async goToInstanceFormView(instance_id) {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: _t('Backup history'),
            target: 'current',
            res_id: instance_id,
            res_model: 'db.backup.instance',
            views: [[false, 'form']],
        });
    }
    async goToInstanceTreeView(config_id, show_all = false) {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: _t('Backup history'),
            target: 'current',
            res_model: 'db.backup.instance',
            views: [[false, 'list'], [false, 'form']],
            domain: show_all ? [['manager_id', '=', config_id], ["active", "in", [false, true]]] : [['manager_id', '=', config_id]]
        });
    }
    async goToConfigFormView(config_id) {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: _t('Backup configuration'),
            target: 'current',
            res_id: config_id,
            res_model: 'db.backup.configure',
            views: [[false, 'form']],
        });
    }
    async goToConfigTreeView() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: _t('Backup configurations'),
            target: 'current',
            res_model: 'db.backup.configure',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        });
    }
    async goToInstanceGlobalTreeView() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: _t('Backup history'),
            target: 'current',
            res_model: 'db.backup.instance',
            views: [[false, 'list'], [false, 'form']]
        });
    }
    toggleMenu(menuId) {
        const menu = document.getElementById(menuId);
        // Closes the active menu, if any
        if (this.state.activeMenu && this.state.activeMenu !== menu) {
            this.state.activeMenu.classList.remove('active');
        }
        // Toggles the state of the clicked menu
        menu.classList.toggle('active');
        if (menu.classList.contains('active')) {
            this.state.activeMenu = menu;
        } else {
            this.state.activeMenu = null;
        }
    }
    restorer(instance_id) {
        this.actionService.doAction({
            name: _t("Restore the database"),
            type: 'ir.actions.act_window',
            res_model: 'db.restore.instance.wizard',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            context: {
                default_backup_id: instance_id
            },
            target: 'new',
        });
    }
    async download(instance_id) {
        let action = await this.orm.call("db.backup.instance", "download_backup", [instance_id]);
        this.actionService.doAction(action);
    }
    async deletion(instance_id, file_exist) {
        await this.actionService.doAction({
            name: _t("Delete the backup"),
            type: 'ir.actions.act_window',
            res_model: 'db.delete.instance',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            context: {
                default_backup_id: instance_id,
                default_file_exist: file_exist,
            },
            target: 'new',
        });
        await this.loadDatas();
    }
}

BackupRestoreDashboardView.template = "krt_backup_manager.BackupRestoreDashboard";
BackupRestoreDashboardView.components = {
    MessageContainer: MessageZoneComponent,
    Many2XAutocomplete: Many2XAutocomplete,
    DateTimeInput: DateTimeInput
};
BackupRestoreDashboardView.props = {
    ...standardActionServiceProps
};
registry.category("actions").add("action_krt_backup_manager_backup_restore_dashboard", BackupRestoreDashboardView, { force: true });
