// Modbus 服务器 Web 控制台

class ModbusConsole {
    constructor() {
        this.ws = null;
        this.currentSlaveId = null;
        this.editingData = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSlaves();
        this.connectWebSocket();
        this.loadTheme();
    }

    setupEventListeners() {
        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // 刷新按钮
        document.getElementById('refresh-btn').addEventListener('click', () => this.loadData());

        // 从站选择
        document.getElementById('slave-select').addEventListener('change', (e) => {
            this.currentSlaveId = e.target.value;
            this.loadData();
        });

        // 主题切换
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());

        // 编辑对话框
        document.getElementById('edit-save-btn').addEventListener('click', () => this.saveEdit());
        document.getElementById('edit-cancel-btn').addEventListener('click', () => this.closeEditDialog());

        // 历史记录按钮
        document.getElementById('clear-history-btn').addEventListener('click', () => this.clearHistory());
        document.getElementById('export-history-btn').addEventListener('click', () => this.exportHistory());

        // 文件记录操作按钮
        document.getElementById('read-file-record-btn').addEventListener('click', () => this.readFileRecord());
        document.getElementById('write-file-record-btn').addEventListener('click', () => this.writeFileRecord());
        
        // 字符串操作按钮
        document.getElementById('write-string-btn').addEventListener('click', () => this.writeString());
        document.getElementById('read-string-btn').addEventListener('click', () => this.readString());
        
        // 配置管理按钮（使用可选链避免元素不存在时报错）
        document.getElementById('refresh-config-btn')?.addEventListener('click', () => this.loadConfig());
        document.getElementById('resize-btn')?.addEventListener('click', () => this.resizeSlave());
    }

    switchTab(tabName) {
        // 更新标签按钮
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // 更新内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });

        // 加载相应数据
        if (tabName === 'history') {
            this.loadHistory();
        } else if (tabName === 'stats') {
            this.loadStats();
        } else if (tabName === 'config') {
            this.loadConfig();
        }
    }

    async loadSlaves() {
        try {
            const response = await fetch('/api/slaves');
            const data = await response.json();
            const select = document.getElementById('slave-select');
            select.innerHTML = '';

            data.slaves.forEach(id => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = `从站 ${id}`;
                select.appendChild(option);
            });

            if (data.slaves.length > 0) {
                this.currentSlaveId = data.slaves[0];
                this.loadData();
            }
        } catch (error) {
            console.error('加载从站列表失败:', error);
        }
    }

    async loadData() {
        if (!this.currentSlaveId) return;

        try {
            const response = await fetch(`/api/data?slave_id=${this.currentSlaveId}`);
            const data = await response.json();
            this.renderData(data);
            this.updateLastUpdate();
        } catch (error) {
            console.error('加载数据失败:', error);
        }
    }

    renderData(data) {
        this.renderBooleanData('coils-grid', data.coils, 'coils');
        this.renderBooleanData('discrete-inputs-grid', data.discrete_inputs, 'discrete_inputs');
        this.renderRegisterData('holding-registers-grid', data.holding_registers, 'holding_registers');
        this.renderRegisterData('input-registers-grid', data.input_registers, 'input_registers');
    }

    renderBooleanData(containerId, values, dataType) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        if (!values || values.length === 0) {
            container.textContent = '无数据';
            return;
        }

        values.forEach((value, index) => {
            const item = document.createElement('div');
            item.className = `data-item boolean ${value ? 'on' : 'off'}`;
            item.innerHTML = `
                <div class="address">${index}</div>
                <div class="value">${value ? 'ON' : 'OFF'}</div>
            `;
            if (dataType === 'coils') {
                item.addEventListener('click', () => this.editValue(dataType, index, value));
            }
            container.appendChild(item);
        });
    }

    renderRegisterData(containerId, values, dataType) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        if (!values || values.length === 0) {
            container.textContent = '无数据';
            return;
        }

        values.forEach((value, index) => {
            const item = document.createElement('div');
            item.className = 'data-item register';
            item.innerHTML = `
                <div class="address">${index}</div>
                <div class="value">${value}</div>
            `;
            if (dataType === 'holding_registers') {
                item.addEventListener('click', () => this.editValue(dataType, index, value));
            }
            container.appendChild(item);
        });
    }

    editValue(dataType, address, currentValue) {
        this.editingData = { dataType, address, currentValue };

        document.getElementById('edit-dialog-title').textContent = 
            `编辑 ${dataType === 'coils' ? '线圈' : '寄存器'}`;
        document.getElementById('edit-address').textContent = address;
        document.getElementById('edit-value').value = currentValue;

        document.getElementById('edit-dialog').classList.add('show');
    }

    async saveEdit() {
        if (!this.editingData) return;

        const { dataType, address } = this.editingData;
        const newValue = document.getElementById('edit-value').value;

        try {
            const endpoint = dataType === 'coils' ? '/api/write/coil' : '/api/write/register';
            const value = dataType === 'coils' ? (newValue === 'true' || newValue === '1') : parseInt(newValue);

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    slave_id: parseInt(this.currentSlaveId),
                    address: address,
                    value: value
                })
            });

            if (response.ok) {
                this.closeEditDialog();
                this.loadData();
            } else {
                alert('保存失败');
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败: ' + error.message);
        }
    }

    closeEditDialog() {
        document.getElementById('edit-dialog').classList.remove('show');
        this.editingData = null;
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history?limit=100');
            const data = await response.json();
            this.renderHistory(data.history);
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    }

    renderHistory(history) {
        const container = document.getElementById('history-list');
        container.innerHTML = '';

        if (!history || history.length === 0) {
            container.textContent = '无历史记录';
            return;
        }

        history.reverse().forEach(record => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-time">${new Date(record.timestamp).toLocaleString()}</div>
                <div class="history-detail">
                    从站 ${record.slave_id} | ${record.data_type} | 地址 ${record.address}
                    <br>
                    ${record.old_value} → ${record.new_value} (来源: ${record.source})
                </div>
            `;
            container.appendChild(item);
        });
    }

    clearHistory() {
        if (confirm('确定要清空历史记录吗？')) {
            document.getElementById('history-list').innerHTML = '<p>历史记录已清空</p>';
        }
    }

    exportHistory() {
        // 导出历史记录为 JSON 文件
        fetch('/api/history?limit=1000')
            .then(response => response.json())
            .then(data => {
                const blob = new Blob([JSON.stringify(data.history, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `modbus_history_${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
            });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            this.renderStats(stats);
        } catch (error) {
            console.error('加载统计信息失败:', error);
        }
    }

    renderStats(stats) {
        document.getElementById('total-requests').textContent = stats.total_requests || 0;
        document.getElementById('successful-requests').textContent = stats.successful_requests || 0;

        const successRate = stats.total_requests > 0
            ? ((stats.successful_requests / stats.total_requests) * 100).toFixed(2)
            : 0;
        document.getElementById('success-rate').textContent = successRate + '%';

        // 功能码名称映射
        const functionCodeNames = {
            'FC01': '读线圈',
            'FC02': '读离散输入',
            'FC03': '读保持寄存器',
            'FC04': '读输入寄存器',
            'FC05': '写单个线圈',
            'FC06': '写单个寄存器',
            'FC07': '读异常状态',
            'FC08': '诊断',
            'FC11': '获取通信事件计数器',
            'FC12': '获取通信事件日志',
            'FC15': '写多个线圈',
            'FC16': '写多个寄存器',
            'FC17': '报告从站ID',
            'FC20': '读文件记录',
            'FC21': '写文件记录',
            'FC22': '屏蔽写寄存器',
            'FC23': '读写多个寄存器',
            'FC24': '读FIFO队列'
        };

        // 功能码统计
        const tbody = document.querySelector('#function-codes-table tbody');
        tbody.innerHTML = '';

        // 按功能码编号排序
        const sortedFCs = Object.entries(stats.function_codes || {}).sort((a, b) => {
            const numA = parseInt(a[0].replace('FC', ''), 10);
            const numB = parseInt(b[0].replace('FC', ''), 10);
            return numA - numB;
        });

        sortedFCs.forEach(([fc, count]) => {
            const row = tbody.insertRow();
            const fcName = functionCodeNames[fc] || '未知功能';
            row.insertCell(0).textContent = `${fc} - ${fcName}`;
            row.insertCell(1).textContent = count;
        });

        // 如果没有统计数据，显示提示
        if (sortedFCs.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 2;
            cell.textContent = '暂无统计数据';
            cell.style.textAlign = 'center';
            cell.style.color = '#999';
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket 已连接');
            document.getElementById('connection-status').textContent = '已连接';
            document.getElementById('connection-status').className = 'status connected';
            this.ws.send(JSON.stringify({ type: 'subscribe' }));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'data_change') {
                // 数据变化通知
                if (data.slave_id === parseInt(this.currentSlaveId)) {
                    this.loadData();
                }
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket 已断开');
            document.getElementById('connection-status').textContent = '未连接';
            document.getElementById('connection-status').className = 'status disconnected';
            // 5秒后重连
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
        };
    }

    toggleTheme() {
        const body = document.body;
        const isDark = body.classList.toggle('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        document.getElementById('theme-toggle').textContent = isDark ? '☀️ 明亮模式' : '🌙 暗黑模式';
    }

    loadTheme() {
        const theme = localStorage.getItem('theme');
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
            document.getElementById('theme-toggle').textContent = '☀️ 明亮模式';
        }
    }

    updateLastUpdate() {
        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    }

    // 文件记录操作
    async readFileRecord() {
        const slaveId = parseInt(document.getElementById('read-slave-id').value);
        const fileNumber = parseInt(document.getElementById('read-file-number').value);
        const recordNumber = parseInt(document.getElementById('read-record-number').value);
        const recordLength = parseInt(document.getElementById('read-record-length').value);

        if (!slaveId || fileNumber < 0 || recordNumber < 0 || recordLength < 1) {
            this.showFileRecordResult('请填写有效的参数', 'error');
            return;
        }

        const resultBox = document.getElementById('file-record-result');
        resultBox.innerHTML = '<p class="text-muted">⏳ 正在读取...</p>';
        resultBox.className = 'result-box';

        try {
            // 使用 FC03 读取保持寄存器（因为文件记录映射到保持寄存器）
            const response = await fetch(`/api/data?slave_id=${slaveId}`);
            if (!response.ok) throw new Error('读取失败');
            
            const data = await response.json();
            const registers = data.holding_registers || [];
            
            // 读取对应的寄存器范围（registers是数组，不是字典）
            const values = [];
            for (let i = 0; i < recordLength; i++) {
                const addr = recordNumber + i;
                values.push(registers[addr] || 0);
            }

            // 尝试将数值解码为字符串
            const decodedString = this.decodeRegistersToString(values);
            const hasValidString = decodedString.replace(/\0/g, '').trim().length > 0;

            // 显示结果
            let resultText = `✅ 读取成功\n\n` +
                `文件编号: ${fileNumber}\n` +
                `记录编号: ${recordNumber}\n` +
                `记录长度: ${recordLength}\n` +
                `数据: [${values.join(', ')}]\n\n` +
                `映射: 保持寄存器 [${recordNumber}-${recordNumber + recordLength - 1}]`;
            
            // 如果能解码为有效字符串，显示字符串内容
            if (hasValidString) {
                const hexValues = values.map(v => '0x' + v.toString(16).toUpperCase().padStart(4, '0'));
                resultText += `\n\n📝 字符串解码:\n` +
                    `文本: "${decodedString}"\n` +
                    `十六进制: [${hexValues.join(', ')}]`;
            }

            this.showFileRecordResult(resultText, 'success');

            // 更新可视化
            this.updateFileRecordVisualization(fileNumber, recordNumber, recordLength, values);

        } catch (error) {
            this.showFileRecordResult(`❌ 读取失败: ${error.message}`, 'error');
        }
    }

    async writeFileRecord() {
        const slaveId = parseInt(document.getElementById('write-slave-id').value);
        const fileNumber = parseInt(document.getElementById('write-file-number').value);
        const recordNumber = parseInt(document.getElementById('write-record-number').value);
        const dataInput = document.getElementById('write-data-values').value;

        if (!slaveId || fileNumber < 0 || recordNumber < 0 || !dataInput.trim()) {
            this.showFileRecordResult('请填写有效的参数', 'error');
            return;
        }

        // 解析数据值
        const values = dataInput.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
        if (values.length === 0) {
            this.showFileRecordResult('数据格式错误，请使用逗号分隔的数字', 'error');
            return;
        }

        const resultBox = document.getElementById('file-record-result');
        resultBox.innerHTML = '<p class="text-muted">⏳ 正在写入...</p>';
        resultBox.className = 'result-box';

        try {
            // 写入每个寄存器
            for (let i = 0; i < values.length; i++) {
                const addr = recordNumber + i;
                const response = await fetch('/api/write/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        slave_id: slaveId,
                        address: addr,
                        value: values[i]
                    })
                });
                
                if (!response.ok) throw new Error(`写入地址 ${addr} 失败`);
            }

            // 显示结果
            this.showFileRecordResult(
                `✅ 写入成功\n\n` +
                `文件编号: ${fileNumber}\n` +
                `记录编号: ${recordNumber}\n` +
                `记录长度: ${values.length}\n` +
                `数据: [${values.join(', ')}]\n\n` +
                `映射: 保持寄存器 [${recordNumber}-${recordNumber + values.length - 1}]`,
                'success'
            );

            // 更新可视化
            this.updateFileRecordVisualization(fileNumber, recordNumber, values.length, values);

        } catch (error) {
            this.showFileRecordResult(`❌ 写入失败: ${error.message}`, 'error');
        }
    }

    showFileRecordResult(message, type = 'info') {
        const resultBox = document.getElementById('file-record-result');
        resultBox.textContent = message;
        resultBox.className = `result-box ${type}`;
    }

    updateFileRecordVisualization(fileNumber, recordNumber, recordLength, values) {
        // 更新参数显示
        document.getElementById('visual-file-number').textContent = fileNumber;
        document.getElementById('visual-record-number').textContent = recordNumber;
        document.getElementById('visual-record-length').textContent = recordLength;

        // 更新地址范围
        document.getElementById('visual-start-address').textContent = recordNumber;
        document.getElementById('visual-end-address').textContent = recordNumber + recordLength - 1;

        // 更新数据网格
        const dataGrid = document.getElementById('visual-data-grid');
        dataGrid.innerHTML = '';

        values.forEach((value, index) => {
            const cell = document.createElement('div');
            cell.className = 'data-cell highlight';
            cell.innerHTML = `
                <div class="cell-label">地址 ${recordNumber + index}</div>
                <div class="cell-value">${value}</div>
            `;
            dataGrid.appendChild(cell);

            // 移除高亮动画
            setTimeout(() => {
                cell.classList.remove('highlight');
            }, 1000);
        });
    }

    // 字符串操作
    async writeString() {
        const slaveId = parseInt(document.getElementById('string-slave-id').value);
        const address = parseInt(document.getElementById('string-address').value);
        const text = document.getElementById('string-text').value;

        if (!slaveId || address < 0 || !text) {
            this.showFileRecordResult('请填写有效的参数', 'error');
            return;
        }

        const resultBox = document.getElementById('file-record-result');
        resultBox.innerHTML = '<p class="text-muted">⏳ 正在写入字符串...</p>';
        resultBox.className = 'result-box';

        try {
            const response = await fetch('/api/write/string', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    slave_id: slaveId,
                    address: address,
                    text: text
                })
            });

            if (!response.ok) throw new Error('写入失败');
            
            const data = await response.json();
            
            this.showFileRecordResult(
                `✅ 字符串写入成功\n\n` +
                `文本: "${text}"\n` +
                `长度: ${data.text_length} 字符\n` +
                `寄存器数: ${data.registers_written}\n` +
                `地址范围: ${data.address_range}\n\n` +
                `编码: 每2个字符占1个寄存器`,
                'success'
            );

        } catch (error) {
            this.showFileRecordResult(`❌ 写入失败: ${error.message}`, 'error');
        }
    }

    async readString() {
        const slaveId = parseInt(document.getElementById('read-string-slave-id').value);
        const address = parseInt(document.getElementById('read-string-address').value);
        const length = parseInt(document.getElementById('read-string-length').value);

        if (!slaveId || address < 0 || length < 1) {
            this.showFileRecordResult('请填写有效的参数', 'error');
            return;
        }

        const resultBox = document.getElementById('file-record-result');
        resultBox.innerHTML = '<p class="text-muted">⏳ 正在读取字符串...</p>';
        resultBox.className = 'result-box';

        try {
            const response = await fetch(`/api/read/string?slave_id=${slaveId}&address=${address}&length=${length}`);
            if (!response.ok) throw new Error('读取失败');
            
            const data = await response.json();
            
            // 将寄存器值转换为十六进制显示
            const hexRegs = data.registers.map(r => '0x' + r.toString(16).toUpperCase().padStart(4, '0'));
            
            this.showFileRecordResult(
                `✅ 字符串读取成功\n\n` +
                `文本: "${data.text}"\n` +
                `长度: ${data.length} 字符\n` +
                `地址范围: ${data.address_range}\n` +
                `寄存器数: ${data.registers.length}\n\n` +
                `寄存器值 (十进制):\n[${data.registers.join(', ')}]\n\n` +
                `寄存器值 (十六进制):\n[${hexRegs.join(', ')}]`,
                'success'
            );

        } catch (error) {
            this.showFileRecordResult(`❌ 读取失败: ${error.message}`, 'error');
        }
    }

    // 辅助方法：将寄存器数组解码为字符串
    decodeRegistersToString(registers) {
        let text = '';
        for (const reg of registers) {
            // 高字节
            const high = (reg >> 8) & 0xFF;
            // 低字节
            const low = reg & 0xFF;
            
            // 只添加可打印的ASCII字符 (32-126)
            if (high >= 32 && high <= 126) {
                text += String.fromCharCode(high);
            } else if (high !== 0) {
                text += '?';  // 不可打印字符用?替代
            }
            
            if (low >= 32 && low <= 126) {
                text += String.fromCharCode(low);
            } else if (low !== 0) {
                text += '?';
            }
        }
        return text;
    }

    // 辅助方法：检查寄存器是否包含有效字符串
    isValidString(registers) {
        for (const reg of registers) {
            const high = (reg >> 8) & 0xFF;
            const low = reg & 0xFF;
            // 如果包含任何可打印ASCII字符，就认为可能是字符串
            if ((high >= 32 && high <= 126) || (low >= 32 && low <= 126)) {
                return true;
            }
        }
        return false;
    }

    // 配置管理
    async loadConfig() {
        try {
            const slaveId = parseInt(document.getElementById('resize-slave-id').value);
            const response = await fetch(`/api/config?slave_id=${slaveId}`);
            if (!response.ok) throw new Error('获取配置失败');
            
            const config = await response.json();
            
            const display = document.getElementById('current-config');
            display.innerHTML = `
                <div class="config-info">
                    <h4>从站 ${config.slave_id} 当前配置</h4>
                    <table class="config-table">
                        <tr>
                            <td><strong>线圈数量:</strong></td>
                            <td>${config.coils}</td>
                        </tr>
                        <tr>
                            <td><strong>离散输入数量:</strong></td>
                            <td>${config.discrete_inputs}</td>
                        </tr>
                        <tr>
                            <td><strong>保持寄存器数量:</strong></td>
                            <td>${config.holding_registers}</td>
                        </tr>
                        <tr>
                            <td><strong>输入寄存器数量:</strong></td>
                            <td>${config.input_registers}</td>
                        </tr>
                    </table>
                </div>
            `;
        } catch (error) {
            const display = document.getElementById('current-config');
            display.innerHTML = `<p class="error">❌ ${error.message}</p>`;
        }
    }

    async resizeSlave() {
        const slaveId = parseInt(document.getElementById('resize-slave-id').value);
        const coils = document.getElementById('resize-coils').value;
        const discreteInputs = document.getElementById('resize-discrete-inputs').value;
        const holdingRegisters = document.getElementById('resize-holding-registers').value;
        const inputRegisters = document.getElementById('resize-input-registers').value;

        // 构建请求数据（只包含非空字段）
        const data = { slave_id: slaveId };
        if (coils) data.coils = parseInt(coils);
        if (discreteInputs) data.discrete_inputs = parseInt(discreteInputs);
        if (holdingRegisters) data.holding_registers = parseInt(holdingRegisters);
        if (inputRegisters) data.input_registers = parseInt(inputRegisters);

        // 检查是否至少有一个字段需要修改
        if (Object.keys(data).length === 1) {
            this.showResizeResult('请至少填写一个要修改的数值', 'error');
            return;
        }

        const resultBox = document.getElementById('resize-result');
        resultBox.style.display = 'block';
        resultBox.innerHTML = '<p class="text-muted">⏳ 正在调整...</p>';
        resultBox.className = 'result-box';

        try {
            const response = await fetch('/api/config/resize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '调整失败');
            }

            const result = await response.json();
            const cfg = result.new_config;

            this.showResizeResult(
                `✅ 调整成功\n\n` +
                `从站 ID: ${result.slave_id}\n\n` +
                `新配置:\n` +
                `• 线圈: ${cfg.coils}\n` +
                `• 离散输入: ${cfg.discrete_inputs}\n` +
                `• 保持寄存器: ${cfg.holding_registers}\n` +
                `• 输入寄存器: ${cfg.input_registers}`,
                'success'
            );

            // 清空输入框
            document.getElementById('resize-coils').value = '';
            document.getElementById('resize-discrete-inputs').value = '';
            document.getElementById('resize-holding-registers').value = '';
            document.getElementById('resize-input-registers').value = '';

            // 刷新配置显示
            this.loadConfig();

        } catch (error) {
            this.showResizeResult(`❌ 调整失败: ${error.message}`, 'error');
        }
    }

    showResizeResult(message, type) {
        const resultBox = document.getElementById('resize-result');
        resultBox.style.display = 'block';
        resultBox.className = `result-box ${type}`;
        resultBox.innerHTML = `<pre>${message}</pre>`;
    }
}

// 初始化控制台
document.addEventListener('DOMContentLoaded', () => {
    new ModbusConsole();
});
