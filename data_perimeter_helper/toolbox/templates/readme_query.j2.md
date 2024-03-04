<!--
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
-->

## List of queries
{%- for query_doc in list_query_doc %}
* [{{ query_doc['query_name'] }}](#query-name-{{ query_doc['query_name'] }})
{%- endfor %}

{% for query_doc in list_query_doc  -%}
# Query name: {{ query_doc['query_name'] }}

### Query description

{{ query_doc['description'] | safe }}

{%- if query_doc['where_documentation'] is defined and query_doc['where_documentation']|length > 0 %}
### Query results filtering

Below filters are applied:
{%- for filter in (query_doc['where_documentation'] + query_doc['data_processing_documentation'])|unique  %}
- {{ filter | safe }}
{%- endfor %}


{%- endif %}

{%- if query_doc['sql_query'] is defined and query_doc['sql_query']|length > 0 %}


### Query details

<details>
<summary>Athena query</summary>

```sql
{{ query_doc['sql_query'] | safe }}
```
</details>

{%- set data_processing_documentation_defined = query_doc['data_processing_documentation'] is defined and query_doc['data_processing_documentation']|length > 0 -%}
{%- set only_in_data_processing_documentation_defined = query_doc['only_in_data_processing_doc'] is defined and query_doc['only_in_data_processing_doc']|length > 0 -%}

{%- if data_processing_documentation_defined or only_in_data_processing_documentation_defined %}

<details>
<summary>Post-Athena data processing</summary>

{% for filter in query_doc['only_in_data_processing_doc']  -%}
- {{ filter | safe }}
{%- endfor %}
{%- for filter in query_doc['data_processing_documentation']  %}
- {{ filter | safe }}
{%- endfor %}
</details>
{%- endif %}
{%- endif %}



{% endfor %}