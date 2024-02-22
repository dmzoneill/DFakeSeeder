def generate_child_entries(fields):
    entries = []
    field_list = fields.split(",")

    for i, field in enumerate(field_list):
        field_id = field.replace(" ", "_")
        label_id = f"notebook_status_{field_id}_label"
        value_id = f"notebook_status_{field_id}_value"

        label_entry = f"""
        <child>
            <object class="GtkLabel" id="{label_id}">
                <property name="visible">True</property>
                <property name="can-focus">False</property>
                <property name="label">{field}</property>
                <property name="xalign">0</property>
                <property name="margin-left">15</property>
                <property name="margin-right">50</property>
            </object>
            <packing>
                <property name="left-attach">{i % 2}</property>
                <property name="top-attach">{i // 2}</property>
            </packing>
        </child>
        """

        value_entry = f"""
        <child>
            <object class="GtkLabel" id="{value_id}">
                <property name="visible">True</property>
                <property name="can-focus">False</property>
                <property name="label">-</property>
                <property name="xalign">0</property>
                <property name="margin-left">15</property>
                <property name="margin-right">50</property>
            </object>
            <packing>
                <property name="left-attach">{(i % 2) + 1}</property>
                <property name="top-attach">{i // 2}</property>
            </packing>
        </child>
        """

        entries.append(label_entry)
        entries.append(value_entry)

    return "".join(entries)


fields = "downspeed,up speed,downloaded,uploaded,seeds,peers,share ratio,availability,seed rank,eta time,active time,seeding time,last transfer,complete seen"
print(generate_child_entries(fields))
