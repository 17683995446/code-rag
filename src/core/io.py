"""
数据导入导出模块 - 产品级
支持JSON、YAML、CSV格式的数据交换
站在巨人的肩膀上 - 使用pyyaml
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict
from datetime import datetime

from .logger import get_logger
from .settings import get_settings

logger = get_logger(__name__)

# 尝试导入yaml，如果失败则使用fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("yaml not available, YAML import/export disabled")


class DataExporter:
    """
    数据导出器
    支持多种格式导出
    """

    def __init__(self):
        self.settings = get_settings()

    def export_json(self, data: Union[List, Dict],
                   output_file: str,
                   indent: int = 2) -> bool:
        """导出为JSON格式"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"JSON导出成功: {output_file}")
            return True
        except Exception as e:
            logger.error(f"JSON导出失败: {e}")
            return False

    def export_yaml(self, data: Union[List, Dict],
                   output_file: str) -> bool:
        """导出为YAML格式"""
        if not YAML_AVAILABLE:
            logger.warning("yaml not available, falling back to JSON")
            json_file = output_file.replace('.yaml', '.json').replace('.yml', '.json')
            return self.export_json(data, json_file)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"YAML导出成功: {output_file}")
            return True
        except Exception as e:
            logger.error(f"YAML导出失败: {e}")
            return False

    def export_csv(self, data: List[Dict],
                  output_file: str) -> bool:
        """导出为CSV格式"""
        if not data:
            logger.warning("无数据可导出")
            return False

        try:
            # 获取所有字段
            fieldnames = set()
            for item in data:
                if isinstance(item, dict):
                    fieldnames.update(item.keys())

            fieldnames = sorted(list(fieldnames))

            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"CSV导出成功: {output_file}")
            return True
        except Exception as e:
            logger.error(f"CSV导出失败: {e}")
            return False

    def export_index_metadata(self, index_data: Dict,
                            output_dir: str) -> bool:
        """导出索引元数据"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        metadata = {
            'export_time': datetime.now().isoformat(),
            'version': self.settings.__version__ if hasattr(self.settings, '__version__') else '3.0.0',
            'document_count': len(index_data.get('documents', [])),
            'metadata': index_data.get('metadata', {})
        }

        # 导出元数据
        self.export_json(metadata, str(output_path / 'metadata.json'))

        # 导出文档
        if 'documents' in index_data:
            self.export_json(
                index_data['documents'],
                str(output_path / 'documents.json')
            )

        logger.info(f"索引元数据导出成功: {output_dir}")
        return True


class DataImporter:
    """
    数据导入器
    支持多种格式导入
    """

    def __init__(self):
        self.settings = get_settings()

    def import_json(self, input_file: str) -> Optional[Union[List, Dict]]:
        """从JSON导入"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"JSON导入成功: {input_file}, {len(data) if isinstance(data, list) else 'dict'} 条")
            return data
        except Exception as e:
            logger.error(f"JSON导入失败: {e}")
            return None

    def import_yaml(self, input_file: str) -> Optional[Union[List, Dict]]:
        """从YAML导入"""
        if not YAML_AVAILABLE:
            logger.warning("yaml not available, trying JSON fallback")
            json_file = input_file.replace('.yaml', '.json').replace('.yml', '.json')
            if Path(json_file).exists():
                return self.import_json(json_file)
            return None
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"YAML导入成功: {input_file}")
            return data
        except Exception as e:
            logger.error(f"YAML导入失败: {e}")
            return None

    def import_csv(self, input_file: str) -> Optional[List[Dict]]:
        """从CSV导入"""
        try:
            data = []
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(dict(row))
            logger.info(f"CSV导入成功: {input_file}, {len(data)} 条")
            return data
        except Exception as e:
            logger.error(f"CSV导入失败: {e}")
            return None

    def import_index_metadata(self, input_dir: str) -> Optional[Dict]:
        """导入索引元数据"""
        input_path = Path(input_dir)

        metadata_file = input_path / 'metadata.json'
        documents_file = input_path / 'documents.json'

        if not metadata_file.exists():
            logger.error(f"元数据文件不存在: {metadata_file}")
            return None

        # 读取元数据
        metadata = self.import_json(str(metadata_file))

        # 读取文档
        documents = None
        if documents_file.exists():
            documents = self.import_json(str(documents_file))

        return {
            'metadata': metadata,
            'documents': documents
        }


class BatchProcessor:
    """
    批量处理器
    支持大规模数据的分批处理
    """

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.settings = get_settings()

    def process_in_batches(self, items: List[Any],
                         processor_func,
                     on_progress=None) -> List[Any]:
        """分批处理"""
        results = []
        total = len(items)
        processed = 0

        for i in range(0, total, self.batch_size):
            batch = items[i:i + self.batch_size]

            try:
                batch_results = processor_func(batch)
                results.extend(batch_results)
                processed += len(batch)

                if on_progress:
                    on_progress(processed, total)

                logger.debug(f"已处理: {processed}/{total}")

            except Exception as e:
                logger.error(f"批次处理失败 (批次 {i//self.batch_size}): {e}")

        return results

    def create_batches(self, items: List[Any]) -> List[List[Any]]:
        """创建批次"""
        batches = []
        for i in range(0, len(items), self.batch_size):
            batches.append(items[i:i + self.batch_size])
        return batches


class DataPipeline:
    """
    数据流水线
    整合导入、转换、导出
    """

    def __init__(self):
        self.exporter = DataExporter()
        self.importer = DataImporter()
        self.batch_processor = BatchProcessor()

    def convert_format(self, input_file: str,
                     output_file: str,
                     input_format: str = 'json',
                     output_format: str = 'yaml') -> bool:
        """格式转换"""
        # 导入
        if input_format == 'json':
            data = self.importer.import_json(input_file)
        elif input_format == 'yaml':
            data = self.importer.import_yaml(input_file)
        elif input_format == 'csv':
            data = self.importer.import_csv(input_file)
        else:
            logger.error(f"不支持的输入格式: {input_format}")
            return False

        if data is None:
            return False

        # 导出
        if output_format == 'json':
            return self.exporter.export_json(data, output_file)
        elif output_format == 'yaml':
            # 如果YAML不可用，我们的 export_yaml 已经会降级到JSON
            return self.exporter.export_yaml(data, output_file)
        elif output_format == 'csv':
            if isinstance(data, list):
                return self.exporter.export_csv(data, output_file)
            else:
                logger.error("CSV导出只支持列表数据")
                return False
        else:
            logger.error(f"不支持的输出格式: {output_format}")
            return False

    def export_with_filter(self, data: List[Dict],
                         output_file: str,
                         filters: Dict[str, Any],
                         format: str = 'json') -> bool:
        """带过滤的导出"""
        # 应用过滤器
        filtered_data = []
        for item in data:
            match = all(
                item.get(key) == value
                for key, value in filters.items()
            )
            if match:
                filtered_data.append(item)

        logger.info(f"过滤后数据: {len(filtered_data)}/{len(data)}")

        # 导出
        if format == 'json':
            return self.exporter.export_json(filtered_data, output_file)
        elif format == 'yaml':
            return self.exporter.export_yaml(filtered_data, output_file)
        elif format == 'csv':
            return self.exporter.export_csv(filtered_data, output_file)
        else:
            return False


# 全局实例
_exporter: Optional[DataExporter] = None
_importer: Optional[DataImporter] = None


def get_exporter() -> DataExporter:
    """获取导出器"""
    global _exporter
    if _exporter is None:
        _exporter = DataExporter()
    return _exporter


def get_importer() -> DataImporter:
    """获取导入器"""
    global _importer
    if _importer is None:
        _importer = DataImporter()
    return _importer


def export_data(data: Union[List, Dict], output_file: str,
               format: str = 'json') -> bool:
    """便捷导出函数"""
    exporter = get_exporter()
    if format == 'json':
        return exporter.export_json(data, output_file)
    elif format == 'yaml':
        return exporter.export_yaml(data, output_file)
    elif format == 'csv':
        if isinstance(data, list):
            return exporter.export_csv(data, output_file)
        return False
    return False


def import_data(input_file: str, format: str = 'json') -> Optional[Union[List, Dict]]:
    """便捷导入函数"""
    importer = get_importer()
    if format == 'json':
        return importer.import_json(input_file)
    elif format == 'yaml':
        return importer.import_yaml(input_file)
    elif format == 'csv':
        return importer.import_csv(input_file)
    return None
